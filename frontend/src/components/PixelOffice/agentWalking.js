import { COFFEE_VISIT_X, COFFEE_VISIT_Y } from './roomDrawing'

// Agent movement state machine — pure logic, no canvas/DOM

export const WALK_SPEED = 150           // px/s
export const DROPOFF_DURATION = 700    // ms
export const PICKUP_DURATION = 500     // ms
export const PROCESS_DURATION = 1800   // ms
export const EXECUTE_DURATION = 2000   // ms
export const COOLDOWN_DURATION = 3000  // ms
export const STUCK_THRESHOLD = 10000
export const IDLE_COFFEE_THRESHOLD = 12000

export const EXAM_INBOX = { x: 430, y: 610 }
export const ACTION_INBOX = { x: 770, y: 610 }

const RD_AGENT_HOMES = {
  sports: { x: 300, y: 225 },
  finance: { x: 900, y: 225 },
  creative: { x: 300, y: 455 },
  tech: { x: 900, y: 455 },
}

const EXAM_HOME = { x: 250, y: 678 }
const EXEC_HOME = { x: 950, y: 678 }

const SPECIAL_AGENTS = ['examination', 'executioner']
const RD_AGENTS = ['sports', 'finance', 'creative', 'tech']
const ALL_AGENTS = [...RD_AGENTS, 'examination', 'executioner']

export function initAgentStates() {
  const states = {}

  RD_AGENTS.forEach(id => {
    const home = RD_AGENT_HOMES[id]
    states[id] = {
      state: 'idle',
      stateStartTime: 0,
      x: home.x,
      y: home.y,
      fromX: home.x,
      fromY: home.y,
      toX: home.x,
      toY: home.y,
      walkDuration: 0,
      carrying: false,
      cooldownUntil: 0,
      completionFlashAt: null,
      stuckSince: null,
      lastActivityAt: 0,
    }
  })

  states.examination = {
    state: 'idle_at_desk',
    stateStartTime: 0,
    x: EXAM_HOME.x,
    y: EXAM_HOME.y,
    fromX: EXAM_HOME.x,
    fromY: EXAM_HOME.y,
    toX: EXAM_HOME.x,
    toY: EXAM_HOME.y,
    walkDuration: 0,
    carrying: false,
    cooldownUntil: 0,
    completionFlashAt: null,
    stuckSince: null,
    lastActivityAt: 0,
  }

  states.executioner = {
    state: 'idle_at_desk',
    stateStartTime: 0,
    x: EXEC_HOME.x,
    y: EXEC_HOME.y,
    fromX: EXEC_HOME.x,
    fromY: EXEC_HOME.y,
    toX: EXEC_HOME.x,
    toY: EXEC_HOME.y,
    walkDuration: 0,
    carrying: false,
    cooldownUntil: 0,
    completionFlashAt: null,
    stuckSince: null,
    lastActivityAt: 0,
  }

  return states
}

export function getWalkDuration(fromX, fromY, toX, toY) {
  const dx = toX - fromX
  const dy = toY - fromY
  const distance = Math.sqrt(dx * dx + dy * dy)
  return (distance / WALK_SPEED) * 1000
}

export function getWalkBob(elapsed) {
  return Math.sin((elapsed / 300) * Math.PI * 2) * 3
}

function transition(agentState, newState, animTime, fromX, fromY, toX, toY) {
  agentState.state = newState
  agentState.stateStartTime = animTime
  agentState.fromX = fromX
  agentState.fromY = fromY
  agentState.toX = toX
  agentState.toY = toY
  agentState.walkDuration = getWalkDuration(fromX, fromY, toX, toY)
}

export function updateAgentStates(states, pipelineStatus, animTime) {
  if (!pipelineStatus) return

  // Update R&D agents
  RD_AGENTS.forEach(agentId => {
    const agentState = states[agentId]
    const agentData = pipelineStatus.agents?.[agentId] || {}
    // For testing: if findings_pending is 0 but has total findings, treat as pending
    let findingsPending = agentData.findings_pending ?? 0
    if (findingsPending === 0 && agentData.findings_total > 0) {
      findingsPending = 1
    }

    const elapsed = animTime - agentState.stateStartTime

    if (!agentState) return

    switch (agentState.state) {
      case 'idle':
        if (findingsPending > 0 && animTime > agentState.cooldownUntil) {
          agentState.lastActivityAt = animTime
          const home = RD_AGENT_HOMES[agentId]
          if (home) {
            transition(agentState, 'walking_to_inbox', animTime, home.x, home.y, EXAM_INBOX.x, EXAM_INBOX.y)
          }
        } else if (findingsPending === 0 && agentState.lastActivityAt > 0 &&
                   animTime - agentState.lastActivityAt > IDLE_COFFEE_THRESHOLD &&
                   animTime > agentState.cooldownUntil) {
          agentState.lastActivityAt = animTime
          const home = RD_AGENT_HOMES[agentId]
          transition(agentState, 'walking_to_coffee', animTime, home.x, home.y, COFFEE_VISIT_X, COFFEE_VISIT_Y)
        }
        break

      case 'walking_to_inbox': {
        const t = Math.min(1, elapsed / agentState.walkDuration)
        agentState.x = agentState.fromX + (agentState.toX - agentState.fromX) * t
        agentState.y = agentState.fromY + (agentState.toY - agentState.fromY) * t
        if (t >= 1) {
          agentState.carrying = true
          transition(agentState, 'dropping_off', animTime, EXAM_INBOX.x, EXAM_INBOX.y, EXAM_INBOX.x, EXAM_INBOX.y)
        }
        break
      }

      case 'dropping_off':
        if (agentState.stuckSince === null) {
          agentState.stuckSince = animTime
          agentState.lastActivityAt = animTime
        }
        if (elapsed >= DROPOFF_DURATION) {
          agentState.carrying = false
          agentState.completionFlashAt = animTime
          agentState.stuckSince = null
          agentState.lastActivityAt = animTime
          const home = RD_AGENT_HOMES[agentId]
          transition(agentState, 'returning', animTime, EXAM_INBOX.x, EXAM_INBOX.y, home.x, home.y)
        }
        break

      case 'returning': {
        const t = Math.min(1, elapsed / agentState.walkDuration)
        agentState.x = agentState.fromX + (agentState.toX - agentState.fromX) * t
        agentState.y = agentState.fromY + (agentState.toY - agentState.fromY) * t
        if (t >= 1) {
          const home = RD_AGENT_HOMES[agentId]
          agentState.x = home.x
          agentState.y = home.y
          agentState.state = 'idle'
          agentState.cooldownUntil = animTime + COOLDOWN_DURATION
        }
        break
      }

      case 'walking_to_coffee': {
        const t = Math.min(1, elapsed / agentState.walkDuration)
        agentState.x = agentState.fromX + (agentState.toX - agentState.fromX) * t
        agentState.y = agentState.fromY + (agentState.toY - agentState.fromY) * t
        if (t >= 1) {
          transition(agentState, 'at_coffee', animTime, COFFEE_VISIT_X, COFFEE_VISIT_Y, COFFEE_VISIT_X, COFFEE_VISIT_Y)
        }
        break
      }

      case 'at_coffee':
        if (elapsed >= 2000) {
          const home = RD_AGENT_HOMES[agentId]
          transition(agentState, 'returning', animTime, COFFEE_VISIT_X, COFFEE_VISIT_Y, home.x, home.y)
          agentState.cooldownUntil = animTime + 5000
        }
        break
    }
  })

  // Update examination agent
  {
    const agentState = states.examination
    const agentData = pipelineStatus.agents?.examination || {}
    const examsPending = agentData.pending_examinations ?? 0

    const elapsed = animTime - agentState.stateStartTime

    switch (agentState.state) {
      case 'idle_at_desk':
        if (examsPending > 0 && animTime > agentState.cooldownUntil) {
          transition(agentState, 'walking_to_pickup', animTime, EXAM_HOME.x, EXAM_HOME.y, EXAM_INBOX.x, EXAM_INBOX.y)
        }
        break

      case 'walking_to_pickup': {
        const t = Math.min(1, elapsed / agentState.walkDuration)
        agentState.x = agentState.fromX + (agentState.toX - agentState.fromX) * t
        agentState.y = agentState.fromY + (agentState.toY - agentState.fromY) * t
        if (t >= 1) {
          transition(agentState, 'at_pickup', animTime, EXAM_INBOX.x, EXAM_INBOX.y, EXAM_INBOX.x, EXAM_INBOX.y)
        }
        break
      }

      case 'at_pickup':
        if (elapsed >= PICKUP_DURATION) {
          agentState.carrying = true
          transition(agentState, 'returning_with_doc', animTime, EXAM_INBOX.x, EXAM_INBOX.y, EXAM_HOME.x, EXAM_HOME.y)
        }
        break

      case 'returning_with_doc': {
        const t = Math.min(1, elapsed / agentState.walkDuration)
        agentState.x = agentState.fromX + (agentState.toX - agentState.fromX) * t
        agentState.y = agentState.fromY + (agentState.toY - agentState.fromY) * t
        if (t >= 1) {
          agentState.x = EXAM_HOME.x
          agentState.y = EXAM_HOME.y
          transition(agentState, 'processing_at_desk', animTime, EXAM_HOME.x, EXAM_HOME.y, EXAM_HOME.x, EXAM_HOME.y)
        }
        break
      }

      case 'processing_at_desk':
        if (agentState.stuckSince === null) {
          agentState.stuckSince = animTime
          agentState.lastActivityAt = animTime
        }
        if (elapsed >= PROCESS_DURATION) {
          agentState.completionFlashAt = animTime
          agentState.stuckSince = null
          agentState.lastActivityAt = animTime
          transition(agentState, 'walking_to_deliver', animTime, EXAM_HOME.x, EXAM_HOME.y, ACTION_INBOX.x, ACTION_INBOX.y)
        }
        break

      case 'walking_to_deliver': {
        const t = Math.min(1, elapsed / agentState.walkDuration)
        agentState.x = agentState.fromX + (agentState.toX - agentState.fromX) * t
        agentState.y = agentState.fromY + (agentState.toY - agentState.fromY) * t
        if (t >= 1) {
          transition(agentState, 'at_delivery', animTime, ACTION_INBOX.x, ACTION_INBOX.y, ACTION_INBOX.x, ACTION_INBOX.y)
        }
        break
      }

      case 'at_delivery':
        if (elapsed >= DROPOFF_DURATION) {
          agentState.carrying = false
          transition(agentState, 'returning_to_desk', animTime, ACTION_INBOX.x, ACTION_INBOX.y, EXAM_HOME.x, EXAM_HOME.y)
        }
        break

      case 'returning_to_desk': {
        const t = Math.min(1, elapsed / agentState.walkDuration)
        agentState.x = agentState.fromX + (agentState.toX - agentState.fromX) * t
        agentState.y = agentState.fromY + (agentState.toY - agentState.fromY) * t
        if (t >= 1) {
          agentState.x = EXAM_HOME.x
          agentState.y = EXAM_HOME.y
          agentState.state = 'idle_at_desk'
          agentState.cooldownUntil = animTime + COOLDOWN_DURATION
        }
        break
      }
    }
  }

  // Update executioner agent
  {
    const agentState = states.executioner
    const agentData = pipelineStatus.agents?.executioner || {}
    const actionsPending = agentData.pending_actions ?? 0

    const elapsed = animTime - agentState.stateStartTime

    switch (agentState.state) {
      case 'idle_at_desk':
        if (actionsPending > 0 && animTime > agentState.cooldownUntil) {
          transition(agentState, 'walking_to_inbox', animTime, EXEC_HOME.x, EXEC_HOME.y, ACTION_INBOX.x, ACTION_INBOX.y)
        }
        break

      case 'walking_to_inbox': {
        const t = Math.min(1, elapsed / agentState.walkDuration)
        agentState.x = agentState.fromX + (agentState.toX - agentState.fromX) * t
        agentState.y = agentState.fromY + (agentState.toY - agentState.fromY) * t
        if (t >= 1) {
          transition(agentState, 'at_inbox', animTime, ACTION_INBOX.x, ACTION_INBOX.y, ACTION_INBOX.x, ACTION_INBOX.y)
        }
        break
      }

      case 'at_inbox':
        if (elapsed >= PICKUP_DURATION) {
          agentState.carrying = true
          transition(agentState, 'returning_with_doc', animTime, ACTION_INBOX.x, ACTION_INBOX.y, EXEC_HOME.x, EXEC_HOME.y)
        }
        break

      case 'returning_with_doc': {
        const t = Math.min(1, elapsed / agentState.walkDuration)
        agentState.x = agentState.fromX + (agentState.toX - agentState.fromX) * t
        agentState.y = agentState.fromY + (agentState.toY - agentState.fromY) * t
        if (t >= 1) {
          agentState.x = EXEC_HOME.x
          agentState.y = EXEC_HOME.y
          transition(agentState, 'executing_at_desk', animTime, EXEC_HOME.x, EXEC_HOME.y, EXEC_HOME.x, EXEC_HOME.y)
        }
        break
      }

      case 'executing_at_desk':
        if (agentState.stuckSince === null) {
          agentState.stuckSince = animTime
          agentState.lastActivityAt = animTime
        }
        if (elapsed >= EXECUTE_DURATION) {
          agentState.carrying = false
          agentState.completionFlashAt = animTime
          agentState.stuckSince = null
          agentState.lastActivityAt = animTime
          agentState.state = 'idle_at_desk'
          agentState.cooldownUntil = animTime + COOLDOWN_DURATION
        }
        break
    }
  }
}
