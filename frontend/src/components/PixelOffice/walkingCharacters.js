import * as canvasHelpers from './canvasHelpers'
import * as pixelArtCharacters from './pixelArtCharacters'
import { getWalkBob } from './agentWalking'

const AGENT_COLORS = {
  sports: '#3b82f6',
  finance: '#10b981',
  creative: '#a855f7',
  tech: '#f97316',
  examination: '#f59e0b',
  executioner: '#ef4444',
}

export function drawExaminationAgentWalking(ctx, x, y) {
  ctx.fillStyle = '#6366f1'
  ctx.fillRect(x + 13, y + 2, 13, 16)
  ctx.fillStyle = '#1e1b4b'
  ctx.fillRect(x + 13, y + 18, 13, 10)
  ctx.fillStyle = '#fff'
  ctx.beginPath()
  ctx.arc(x + 19, y + 8, 4, 0, Math.PI * 2)
  ctx.fill()
}

export function drawExecutionerAgentWalking(ctx, x, y) {
  ctx.fillStyle = '#dc2626'
  ctx.fillRect(x + 13, y + 2, 13, 16)
  ctx.fillStyle = '#7f1d1d'
  ctx.fillRect(x + 13, y + 18, 13, 10)
  ctx.fillStyle = '#fff'
  ctx.beginPath()
  ctx.arc(x + 19, y + 8, 4, 0, Math.PI * 2)
  ctx.fill()
  ctx.fillStyle = '#fbbf24'
  ctx.fillRect(x + 16, y + 12, 4, 2)
}

export function drawDocumentProp(ctx, cx, cy) {
  const colors = canvasHelpers.Colors
  ctx.shadowBlur = 3
  ctx.shadowColor = 'rgba(0,0,0,0.4)'
  ctx.shadowOffsetX = 1
  ctx.shadowOffsetY = 1
  ctx.fillStyle = '#f5f5dc'
  ctx.fillRect(cx - 4, cy - 5, 8, 10)
  ctx.shadowBlur = 0
  ctx.fillStyle = '#e2e8f0'
  ctx.fillRect(cx - 2, cy - 3, 4, 1)
  ctx.fillRect(cx - 2, cy - 1, 4, 1)
  ctx.fillRect(cx - 2, cy + 1, 4, 1)
}

export function drawWalkingAgent(ctx, agentId, agentState, animTime) {
  const AGENT_LABELS = {
    sports: 'Sports',
    finance: 'Finance',
    creative: 'Creative',
    tech: 'Tech',
    examination: 'Examiner',
    executioner: 'Executioner',
  }

  const isWalking = agentState.state.includes('walking')
  const elapsed = animTime - agentState.stateStartTime
  const bob = isWalking ? getWalkBob(elapsed) : 0

  const renderX = agentState.x
  const renderY = agentState.y + bob

  const facingLeft = agentState.toX < agentState.fromX

  if (isWalking) {
    const dx = agentState.toX - agentState.fromX
    const dy = agentState.toY - agentState.fromY
    const distance = Math.sqrt(dx * dx + dy * dy)

    if (distance > 0) {
      for (let i = 1; i <= 3; i++) {
        const alpha = 0.22 - i * 0.08
        const trailDist = 8 * i
        const trailX = agentState.x - (dx / distance) * trailDist
        const trailY = agentState.y - (dy / distance) * trailDist
        ctx.fillStyle = AGENT_COLORS[agentId] || '#999'
        ctx.globalAlpha = alpha
        ctx.beginPath()
        ctx.arc(trailX, trailY, 2, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.globalAlpha = 1
    }
  }

  if (facingLeft) {
    ctx.save()
    ctx.translate(renderX * 2, 0)
    ctx.scale(-1, 1)
  }

  const RD_AGENTS = ['sports', 'finance', 'creative', 'tech']
  if (RD_AGENTS.includes(agentId)) {
    pixelArtCharacters.drawRDAgentCharacter(ctx, agentId, renderX - 13, renderY)
  } else if (agentId === 'examination') {
    drawExaminationAgentWalking(ctx, renderX - 19, renderY)
  } else if (agentId === 'executioner') {
    drawExecutionerAgentWalking(ctx, renderX - 19, renderY)
  }

  if (facingLeft) {
    ctx.restore()
  }

  if (agentState.carrying) {
    drawDocumentProp(ctx, agentState.x + 6, agentState.y + 14)
  }

  const label = AGENT_LABELS[agentId] || agentId
  const color = AGENT_COLORS[agentId] || '#999'
  const charCX = agentState.x
  const charY = agentState.y

  const pillY = charY - 20
  const textWidth = label.length * 7
  const pillW = textWidth + 16
  const pillH = 16

  canvasHelpers.drawRoundedRect(ctx, charCX - pillW / 2, pillY - pillH / 2, pillW, pillH, 4, 'rgba(0,0,0,0.75)')
  canvasHelpers.drawText(ctx, label.toUpperCase(), charCX, pillY + 4, 'bold 9px monospace', '#fff', 'center')

  const dotX = charCX + 42
  const dotY = charY - 20
  const pulse = isWalking ? 4 + Math.sin(animTime / 200) : 3
  const dotColor = isWalking ? '#fbbf24' : '#10b981'
  canvasHelpers.drawCircle(ctx, dotX, dotY, pulse, dotColor, 'rgba(0,0,0,0.4)', 1)
}
