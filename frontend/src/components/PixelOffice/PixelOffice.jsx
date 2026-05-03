import { useEffect, useRef, useState } from 'react'
import * as canvasHelpers from './canvasHelpers'
import * as pixelArtCharacters from './pixelArtCharacters'
import * as animationUtils from './animationUtils'
import * as roomDrawing from './roomDrawing'
import {
  initAgentStates,
  updateAgentStates,
  STUCK_THRESHOLD,
  DROPOFF_DURATION,
  PROCESS_DURATION,
  EXECUTE_DURATION,
} from './agentWalking'
import { drawWalkingAgent } from './walkingCharacters'

export default function PixelOffice({ pipelineStatus, findings, examinations, pipelineActions, costs }) {
  const canvasRef = useRef(null)
  const [animTime, setAnimTime] = useState(0)

  const agentStatesRef = useRef(null)
  if (agentStatesRef.current === null) {
    agentStatesRef.current = initAgentStates()
  }

  useEffect(() => {
    let animationFrameId
    const startTime = Date.now()
    const animate = () => {
      const elapsed = Date.now() - startTime
      setAnimTime(elapsed)
      animationFrameId = requestAnimationFrame(animate)
    }
    animationFrameId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationFrameId)
  }, [])

  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    canvas.width = roomDrawing.CANVAS_WIDTH
    canvas.height = roomDrawing.CANVAS_HEIGHT

    updateAgentStates(agentStatesRef.current, pipelineStatus, animTime)
    const states = agentStatesRef.current

    // Computed values
    const examPending = pipelineStatus?.agents?.examination?.pending_examinations ?? 0
    const actionPending = pipelineStatus?.agents?.executioner?.pending_actions ?? 0
    const findingsCount = Object.keys(findings || {}).length
    const completedCount = (Array.isArray(pipelineActions) ? pipelineActions : []).filter(a => a.result !== 'pending').length
    const archiveIsGlowing = Object.values(states).some(s =>
      s.completionFlashAt && (animTime - s.completionFlashAt) < 2000)
    const screenData = {
      findingsCount,
      costTotal: costs?.today?.estimated_usd != null ? costs.today.estimated_usd.toFixed(2) : '--',
      examPending,
      actionPending,
    }

    // 1. Background
    ctx.fillStyle = '#111'
    ctx.fillRect(0, 0, roomDrawing.CANVAS_WIDTH, roomDrawing.CANVAS_HEIGHT)

    // 2. Floor
    roomDrawing.drawFloor(ctx)

    // 3. Wall (with live screen data)
    roomDrawing.drawWall(ctx, screenData)

    // 4. Left-wall furniture
    roomDrawing.drawFileCabinet(ctx, roomDrawing.FILE_CABINET_X, roomDrawing.FILE_CABINET_Y)
    roomDrawing.drawWhiteboard(ctx, roomDrawing.WHITEBOARD_X, roomDrawing.WHITEBOARD_Y, {
      findings: findingsCount,
      examinations: examPending,
    })

    // 5. Right-wall furniture
    roomDrawing.drawCoffeeMachine(ctx, roomDrawing.COFFEE_MACHINE_X, roomDrawing.COFFEE_MACHINE_Y, animTime)
    roomDrawing.drawArchiveShelf(ctx, roomDrawing.ARCHIVE_SHELF_X, roomDrawing.ARCHIVE_SHELF_Y, completedCount, animTime, archiveIsGlowing)

    // 6. Room decor (central table, plants)
    roomDrawing.drawRoomDecor(ctx)

    // 7. R&D agent workstations
    roomDrawing.ROOM_AGENTS.forEach(agent => drawAgentWorkstation(agent))

    // 8. Examination station
    const examCount = (Array.isArray(examinations) ? examinations : []).filter(e => e.status === 'pending_action').length
    drawSpecialStation(roomDrawing.EXAM_AGENT, examCount, 'examination')

    // 9. Executioner station
    const actionCount = (Array.isArray(pipelineActions) ? pipelineActions : []).filter(a => a.result === 'pending').length
    drawSpecialStation(roomDrawing.EXEC_AGENT, actionCount, 'executioner')

    // 10. Floor inbox trays
    roomDrawing.drawFloorInboxTray(ctx, roomDrawing.EXAM_INBOX_X, roomDrawing.EXAM_INBOX_Y, examPending, 'EXAM IN', '#f59e0b')
    roomDrawing.drawFloorInboxTray(ctx, roomDrawing.ACTION_INBOX_X, roomDrawing.ACTION_INBOX_Y, actionPending, 'ACTION IN', '#ef4444')

    // 11. Walking agents second pass (renders on top of all furniture)
    const agentIds = ['sports', 'finance', 'creative', 'tech', 'examination', 'executioner']
    const NON_IDLE = ['idle', 'idle_at_desk']
    agentIds.forEach(id => {
      const agentState = states[id]
      if (agentState && !NON_IDLE.includes(agentState.state)) {
        drawWalkingAgent(ctx, id, agentState, animTime)
      }
    })

    // 12. Completion sparkles
    agentIds.forEach(id => {
      const agentState = states[id]
      if (!agentState?.completionFlashAt) return
      const age = animTime - agentState.completionFlashAt
      const cx = agentState.x
      const cy = agentState.y - 20
      const particles = animationUtils.getSparkleParticles(cx, cy, age)
      if (particles.length > 0) {
        roomDrawing.drawCompletionSparkles(ctx, cx, cy, particles)
      }
    })

    // 13. Stuck warnings
    agentIds.forEach(id => {
      const agentState = states[id]
      if (!agentState?.stuckSince) return
      const stuckFor = animTime - agentState.stuckSince
      if (stuckFor > STUCK_THRESHOLD) {
        const alpha = animationUtils.getStuckWarningAlpha(animTime)
        roomDrawing.drawWarningTriangle(ctx, agentState.x, agentState.y - 30, alpha)
      }
    })

    // 14. Cost meter
    const currentCost = costs?.today?.estimated_usd ?? 0
    roomDrawing.drawCostMeter(
      ctx,
      roomDrawing.COST_METER_X,
      roomDrawing.COST_METER_Y,
      roomDrawing.COST_METER_W,
      roomDrawing.COST_METER_H,
      currentCost,
      roomDrawing.BUDGET_LIMIT,
      animTime
    )

    // Helper: draw R&D agent workstation with glow/progress/stuck layers
    function drawAgentWorkstation(agent) {
      const { id, label, color, deskX, deskY } = agent
      const charCX = deskX + roomDrawing.DESK_W / 2
      const charY = deskY + roomDrawing.DESK_H + 15

      const agentState = states[id]
      const isIdle = !agentState || agentState.state === 'idle'
      const isDropping = agentState?.state === 'dropping_off'
      const isStuck = agentState?.stuckSince && (animTime - agentState.stuckSince) > STUCK_THRESHOLD

      // Desk glow when processing
      if (isDropping) {
        const glowR = animationUtils.getWorkingGlowRadius(animTime)
        roomDrawing.drawDeskWorkingGlow(ctx, deskX, deskY, roomDrawing.DESK_W, roomDrawing.DESK_H, color, glowR)
      }

      roomDrawing.drawDesk(ctx, deskX, deskY, roomDrawing.DESK_W, roomDrawing.DESK_H, color)
      roomDrawing.drawDomainObject(ctx, id, deskX, deskY)

      // Stuck border
      if (isStuck) {
        const ba = animationUtils.getStuckBorderAlpha(animTime)
        roomDrawing.drawStuckDeskBorder(ctx, deskX, deskY, roomDrawing.DESK_W, roomDrawing.DESK_H, ba)
      }

      // Progress bar when dropping off
      if (isDropping) {
        const elapsed = animTime - agentState.stateStartTime
        roomDrawing.drawDeskProgressBar(ctx, deskX, deskY, roomDrawing.DESK_W, elapsed, DROPOFF_DURATION, color)
      }

      if (isIdle) {
        const bob = animationUtils.getIdleBreathePulse(animTime)
        pixelArtCharacters.drawRDAgentCharacter(ctx, id, charCX - 13, charY + bob)
        pixelArtCharacters.drawHeldObject(ctx, id, charCX - 13, charY + bob)
        roomDrawing.drawAgentNameLabel(ctx, charCX, charY, label, color)
        const agentStatus = pipelineStatus?.agents?.[id] || {}
        const isWorking = agentStatus.status === 'working'
        roomDrawing.drawStatusDot(ctx, charCX, charY, isWorking, animTime)
        const finding = findings?.[id]
        if (finding?.finding_text) {
          const bubbleBottomY = deskY - 8
          roomDrawing.drawSpeechBubble(ctx, charCX, bubbleBottomY, finding.finding_text, color)
          roomDrawing.drawImportanceBadge(ctx, charCX + 80, deskY - 35, finding.importance_score)
        }
      }
    }

    function drawSpecialStation(agent, count, type) {
      const { id, label, color, deskX, deskY, deskW = roomDrawing.DESK_W } = agent
      const charCX = deskX + deskW / 2
      const charY = deskY + roomDrawing.DESK_H + 15

      const agentState = states[id]
      const isIdleAtDesk = !agentState || agentState.state === 'idle_at_desk'
      const isProcessing = agentState?.state === (type === 'examination' ? 'processing_at_desk' : 'executing_at_desk')
      const processDuration = type === 'examination' ? PROCESS_DURATION : EXECUTE_DURATION
      const isStuck = agentState?.stuckSince && (animTime - agentState.stuckSince) > STUCK_THRESHOLD

      if (isProcessing) {
        const glowR = animationUtils.getWorkingGlowRadius(animTime)
        roomDrawing.drawDeskWorkingGlow(ctx, deskX, deskY, deskW, roomDrawing.DESK_H, color, glowR)
      }

      roomDrawing.drawDesk(ctx, deskX, deskY, deskW, roomDrawing.DESK_H, color)
      roomDrawing.drawDomainObject(ctx, id, deskX, deskY)

      if (isStuck) {
        const ba = animationUtils.getStuckBorderAlpha(animTime)
        roomDrawing.drawStuckDeskBorder(ctx, deskX, deskY, deskW, roomDrawing.DESK_H, ba)
      }

      if (isProcessing) {
        const elapsed = animTime - agentState.stateStartTime
        roomDrawing.drawDeskProgressBar(ctx, deskX, deskY, deskW, elapsed, processDuration, color)
      }

      if (isIdleAtDesk) {
        if (type === 'examination') {
          pixelArtCharacters.drawExaminationAgent(ctx, charCX - 19, charY)
        } else {
          pixelArtCharacters.drawExecutionerAgent(ctx, charCX - 19, charY)
        }
        roomDrawing.drawAgentNameLabel(ctx, charCX, charY, label, color)
        roomDrawing.drawStatusDot(ctx, charCX, charY, count > 0, animTime)
      }

      if (count > 0) {
        const bubbleText = type === 'examination'
          ? `${count} pending exam${count > 1 ? 's' : ''}`
          : `${count} pending action${count > 1 ? 's' : ''}`
        roomDrawing.drawSpeechBubble(ctx, charCX, deskY - 8, bubbleText, color)
      }
    }
  }, [pipelineStatus, findings, examinations, pipelineActions, costs, animTime])

  return (
    <div className="w-full h-full flex items-center justify-center">
      <canvas
        ref={canvasRef}
        className="block"
        style={{
          maxWidth: '100%',
          maxHeight: '100%',
          imageRendering: 'pixelated',
          width: '100%',
          height: 'auto',
        }}
      />
    </div>
  )
}
