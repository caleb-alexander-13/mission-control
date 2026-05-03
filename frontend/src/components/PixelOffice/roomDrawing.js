import { drawRect, drawRoundedRect, drawCircle, drawText, drawBadge, drawLine, Colors } from './canvasHelpers'

// Layout constants
export const CANVAS_WIDTH = 1200
export const CANVAS_HEIGHT = 800
export const WALL_HEIGHT = 50
export const TILE_SIZE = 40
export const FLOOR_COLOR_A = '#2d5a27'
export const FLOOR_COLOR_B = '#1e4020'
export const WALL_COLOR = '#4a3728'
export const WALL_TRIM = '#6b4c3b'
export const DESK_COLOR = '#8b6f47'
export const DESK_SHADOW = '#5c4a30'
export const DESK_W = 140
export const DESK_H = 70

// Agent layout config
export const ROOM_AGENTS = [
  { id: 'sports', label: 'Sports', color: '#3b82f6', deskX: 230, deskY: 140 },
  { id: 'finance', label: 'Finance', color: '#10b981', deskX: 830, deskY: 140 },
  { id: 'creative', label: 'Creative', color: '#a855f7', deskX: 230, deskY: 370 },
  { id: 'tech', label: 'Tech', color: '#f97316', deskX: 830, deskY: 370 },
]

export const EXAM_AGENT = { id: 'examination', label: 'Examiner', color: '#f59e0b', deskX: 150, deskY: 565, deskW: 200 }
export const EXEC_AGENT = { id: 'executioner', label: 'Executioner', color: '#ef4444', deskX: 850, deskY: 565, deskW: 200 }

export const FILE_CABINET_X = 55;  export const FILE_CABINET_Y = 210
export const WHITEBOARD_X = 55;    export const WHITEBOARD_Y = 310
export const COFFEE_MACHINE_X = 1090; export const COFFEE_MACHINE_Y = 210
export const COFFEE_VISIT_X = 1090;   export const COFFEE_VISIT_Y = 270
export const ARCHIVE_SHELF_X = 1060;  export const ARCHIVE_SHELF_Y = 310
export const COST_METER_X = 500;   export const COST_METER_Y = 710
export const COST_METER_W = 200;   export const COST_METER_H = 16
export const BUDGET_LIMIT = 100
export const LEFT_PANEL_X = 200;   export const RIGHT_PANEL_X = 920
export const PANEL_Y = 8;          export const PANEL_W = 80; export const PANEL_H = 28

// Floor inbox trays
export const EXAM_INBOX_X = 430
export const EXAM_INBOX_Y = 590
export const ACTION_INBOX_X = 770
export const ACTION_INBOX_Y = 590

// Floor pattern: alternating checker tiles with subtle grid overlay
export function drawFloor(ctx) {
  for (let row = 0; row * TILE_SIZE + WALL_HEIGHT < CANVAS_HEIGHT; row++) {
    for (let col = 0; col * TILE_SIZE < CANVAS_WIDTH; col++) {
      const x = col * TILE_SIZE
      const y = WALL_HEIGHT + row * TILE_SIZE
      ctx.fillStyle = (row + col) % 2 === 0 ? FLOOR_COLOR_A : FLOOR_COLOR_B
      ctx.fillRect(x, y, TILE_SIZE, TILE_SIZE)
    }
  }
  // Subtle grid line overlay
  ctx.strokeStyle = 'rgba(0,0,0,0.15)'
  ctx.lineWidth = 0.5
  for (let x = 0; x < CANVAS_WIDTH; x += TILE_SIZE) {
    ctx.beginPath()
    ctx.moveTo(x, WALL_HEIGHT)
    ctx.lineTo(x, CANVAS_HEIGHT)
    ctx.stroke()
  }
  for (let y = WALL_HEIGHT; y < CANVAS_HEIGHT; y += TILE_SIZE) {
    ctx.beginPath()
    ctx.moveTo(0, y)
    ctx.lineTo(CANVAS_WIDTH, y)
    ctx.stroke()
  }
}

// Wall: brown band at top with trim, center text, decorative panels
export function drawWall(ctx, screenData = {}) {
  ctx.fillStyle = WALL_COLOR
  ctx.fillRect(0, 0, CANVAS_WIDTH, WALL_HEIGHT)
  ctx.fillStyle = WALL_TRIM
  ctx.fillRect(0, WALL_HEIGHT - 6, CANVAS_WIDTH, 6)

  // "MISSION CONTROL" sign
  drawText(ctx, 'MISSION CONTROL', CANVAS_WIDTH / 2, 30, 'bold 14px monospace', '#f5d78e', 'center')

  // Left panel: findings + cost
  drawWallPanel(ctx, LEFT_PANEL_X, PANEL_Y,
    [`FINDINGS: ${screenData.findingsCount ?? '--'}`, `COST: $${screenData.costTotal ?? '--'}`],
    '#10b981')
  // Right panel: pipeline status
  drawWallPanel(ctx, RIGHT_PANEL_X, PANEL_Y,
    [`EXAM: ${screenData.examPending ?? '--'}`, `EXEC: ${screenData.actionPending ?? '--'}`],
    '#f59e0b')
}

function drawWallPanel(ctx, x, y, lines, color) {
  ctx.fillStyle = '#0a0f1a'
  ctx.fillRect(x, y, PANEL_W, PANEL_H)
  ctx.strokeStyle = color
  ctx.lineWidth = 1
  ctx.strokeRect(x, y, PANEL_W, PANEL_H)

  // Scanlines every 4px
  ctx.strokeStyle = 'rgba(255,255,255,0.04)'
  ctx.lineWidth = 0.5
  for (let sy = y + 4; sy < y + PANEL_H; sy += 4) {
    ctx.beginPath()
    ctx.moveTo(x, sy)
    ctx.lineTo(x + PANEL_W, sy)
    ctx.stroke()
  }

  // Text lines
  lines.forEach((line, i) => {
    drawText(ctx, line, x + 4, y + 10 + i * 11, '7px monospace', color, 'left')
  })

  // Blinking cursor dot bottom-right
  ctx.fillStyle = color
  ctx.beginPath()
  ctx.arc(x + PANEL_W - 5, y + PANEL_H - 5, 2, 0, Math.PI * 2)
  ctx.fill()
}

// Top-down wooden desk with colored accent stripe
export function drawDesk(ctx, x, y, w = DESK_W, h = DESK_H, agentColor = '#8b6f47') {
  // Shadow
  drawRect(ctx, x + 3, y + 3, w, h, 'rgba(0,0,0,0.4)')

  // Desk surface
  drawRect(ctx, x, y, w, h, DESK_COLOR, DESK_SHADOW, 1)

  // Wood grain lines
  ctx.strokeStyle = 'rgba(0,0,0,0.12)'
  ctx.lineWidth = 1
  for (let gy = y + 10; gy < y + h - 5; gy += 10) {
    ctx.beginPath()
    ctx.moveTo(x + 4, gy)
    ctx.lineTo(x + w - 4, gy)
    ctx.stroke()
  }

  // Colored agent accent stripe on front edge
  ctx.fillStyle = agentColor
  ctx.fillRect(x, y + h - 5, w, 5)

  // Monitor area (left half): dark screen
  const monX = x + 8, monY = y + 8
  drawRect(ctx, monX, monY, 44, 32, '#1a1a2a', '#333', 1)

  // Monitor stand
  drawRect(ctx, monX + 20, monY + 32, 4, 6, '#555')
}

// Domain objects drawn on right side of desk
export function drawDomainObject(ctx, agentId, deskX, deskY) {
  const ox = deskX + DESK_W / 2 + 4
  const oy = deskY + 8

  switch (agentId) {
    case 'sports':
      drawTV(ctx, ox, oy)
      break
    case 'finance':
      drawFinanceMonitor(ctx, ox, oy)
      break
    case 'creative':
      drawChalkboard(ctx, ox, oy)
      break
    case 'tech':
      drawServerRack(ctx, ox, oy)
      break
    case 'examination':
      drawInboxTray(ctx, ox, oy)
      break
    case 'executioner':
      drawConsole(ctx, ox, oy)
      break
  }
}

function drawTV(ctx, x, y) {
  // Screen bezel
  drawRect(ctx, x, y, 44, 32, '#1a1a2a', '#333', 1)
  // Score bars (simplified)
  ctx.fillStyle = '#fbbf24'
  ctx.fillRect(x + 6, y + 12, 6, 8)
  ctx.fillRect(x + 32, y + 16, 6, 4)
  ctx.fillStyle = '#ffffff'
  drawText(ctx, '24', x + 12, y + 18, '9px bold', '#fff', 'center')
  drawText(ctx, '17', x + 32, y + 18, '9px bold', '#fff', 'center')
}

function drawFinanceMonitor(ctx, x, y) {
  drawRect(ctx, x, y, 44, 32, '#0a0a1a', '#333', 1)
  // Ticker line chart in green
  ctx.strokeStyle = '#10b981'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(x + 6, y + 20)
  ctx.lineTo(x + 12, y + 14)
  ctx.lineTo(x + 18, y + 16)
  ctx.lineTo(x + 24, y + 12)
  ctx.lineTo(x + 30, y + 22)
  ctx.lineTo(x + 36, y + 18)
  ctx.stroke()
}

function drawChalkboard(ctx, x, y) {
  drawRect(ctx, x, y, 44, 32, '#2d3a2d', '#4a5c4a', 1)
  // White chalk marks
  ctx.strokeStyle = '#f5f5dc'
  ctx.lineWidth = 1.5
  ctx.lineCap = 'round'

  ctx.beginPath()
  ctx.moveTo(x + 8, y + 10)
  ctx.lineTo(x + 15, y + 20)
  ctx.stroke()

  ctx.beginPath()
  ctx.moveTo(x + 20, y + 8)
  ctx.lineTo(x + 25, y + 22)
  ctx.stroke()

  ctx.beginPath()
  ctx.arc(x + 35, y + 15, 3, 0, Math.PI * 2)
  ctx.stroke()
}

function drawServerRack(ctx, x, y) {
  drawRect(ctx, x, y, 44, 32, '#3a3a3a', '#555', 1)

  // LED rows
  const colors = ['#10b981', '#ef4444', '#10b981', '#fbbf24', '#ef4444', '#10b981', '#ef4444', '#10b981', '#10b981', '#ef4444', '#10b981', '#fbbf24']
  let idx = 0
  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 4; col++) {
      const ledX = x + 8 + col * 10
      const ledY = y + 8 + row * 8
      ctx.fillStyle = colors[idx % colors.length]
      ctx.beginPath()
      ctx.arc(ledX, ledY, 1.5, 0, Math.PI * 2)
      ctx.fill()
      idx++
    }
  }
}

function drawInboxTray(ctx, x, y) {
  // Base tray
  ctx.fillStyle = '#8b7355'
  ctx.fillRect(x, y + 22, 44, 10)

  // Stacked papers
  const paperColor = '#f5f5dc'
  for (let i = 4; i >= 0; i--) {
    ctx.fillStyle = paperColor
    ctx.globalAlpha = 0.6 + (i * 0.08)
    ctx.fillRect(x + 2 + i * 1.5, y + 22 - i * 3, 40, 4)
  }
  ctx.globalAlpha = 1
}

function drawConsole(ctx, x, y) {
  drawRect(ctx, x, y, 44, 32, '#111', '#333', 1)

  // Button grid
  const buttonColors = ['#3b82f6', '#3b82f6', '#ef4444', '#3b82f6', '#ef4444', '#3b82f6', '#3b82f6', '#3b82f6', '#ef4444', '#3b82f6', '#3b82f6', '#3b82f6']
  let idx = 0
  for (let row = 0; row < 3; row++) {
    for (let col = 0; col < 4; col++) {
      const btnX = x + 8 + col * 9
      const btnY = y + 6 + row * 7
      ctx.fillStyle = buttonColors[idx]
      ctx.beginPath()
      ctx.arc(btnX, btnY, 1.5, 0, Math.PI * 2)
      ctx.fill()
      idx++
    }
  }

  // Tiny screen
  ctx.fillStyle = '#001a00'
  ctx.fillRect(x + 8, y + 22, 20, 8)
  ctx.fillStyle = '#10b981'
  ctx.fillRect(x + 10, y + 24, 2, 2)
  ctx.fillRect(x + 14, y + 24, 2, 2)
  ctx.fillRect(x + 18, y + 24, 2, 2)
  ctx.fillRect(x + 22, y + 24, 2, 2)
}

export function drawFileCabinet(ctx, x, y) {
  // Shadow
  drawRect(ctx, x + 3, y + 3, 40, 60, 'rgba(0,0,0,0.4)')
  // Cabinet body
  drawRect(ctx, x, y, 40, 60, '#5c4a30', '#3d2f1f', 1)
  // 3 drawers
  for (let i = 0; i < 3; i++) {
    const dy = y + 4 + i * 18
    drawRect(ctx, x + 3, dy, 34, 14, '#6b5840', '#4a3728', 1)
    // Handle nub
    ctx.fillStyle = '#c8a96e'
    ctx.fillRect(x + 15, dy + 5, 10, 4)
  }
  drawText(ctx, 'ARCHIVE', x + 20, y + 72, '7px monospace', '#8b7355', 'center')
}

export function drawWhiteboard(ctx, x, y, stats = {}) {
  // Frame
  drawRect(ctx, x, y, 60, 50, '#6b4c3b', '#4a3728', 2)
  // Board surface
  drawRect(ctx, x + 4, y + 4, 52, 38, '#f5f0e8')
  // Findings line in blue
  ctx.font = '7px monospace'
  ctx.fillStyle = '#3b82f6'
  ctx.textAlign = 'left'
  ctx.fillText(`F: ${stats.findings ?? 0}`, x + 7, y + 16)
  // Examinations line in amber
  ctx.fillStyle = '#f59e0b'
  ctx.fillText(`E: ${stats.examinations ?? 0}`, x + 7, y + 28)
  // Label below
  drawText(ctx, 'STATUS', x + 30, y + 58, '7px monospace', '#8b7355', 'center')
}

export function drawCoffeeMachine(ctx, x, y, animTime = 0) {
  // Shadow
  drawRect(ctx, x + 3, y + 3, 40, 50, 'rgba(0,0,0,0.4)')
  // Machine body
  drawRect(ctx, x, y, 40, 50, '#2a2a2a', '#444', 1)
  // Water tank (top section)
  drawRect(ctx, x + 4, y + 2, 32, 14, '#1a3a5c', '#2a5a8c', 1)
  // Brew unit (middle)
  drawRect(ctx, x + 8, y + 18, 24, 16, '#333', '#555', 1)
  ctx.fillStyle = '#8b4513'
  ctx.fillRect(x + 12, y + 20, 16, 12)
  // Cup area
  drawRect(ctx, x + 12, y + 36, 16, 10, '#1a1a1a', '#333', 1)
  // Steam puffs
  const steamPhase = Math.sin(animTime / 400)
  const steamAlpha = 0.3 + steamPhase * 0.2
  ctx.globalAlpha = steamAlpha
  ctx.fillStyle = '#cccccc'
  ctx.beginPath()
  ctx.arc(x + 18, y - 4 - steamPhase * 3, 3, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.arc(x + 24, y - 8 - steamPhase * 4, 2, 0, Math.PI * 2)
  ctx.fill()
  ctx.globalAlpha = 1
  drawText(ctx, 'COFFEE', x + 20, y + 58, '7px monospace', '#8b7355', 'center')
}

export function drawArchiveShelf(ctx, x, y, completedCount = 0, animTime = 0, isGlowing = false) {
  // Shadow
  drawRect(ctx, x + 3, y + 3, 80, 80, 'rgba(0,0,0,0.4)')
  // Shelf unit body
  drawRect(ctx, x, y, 80, 80, '#2a1f18', '#1a1208', 1)
  // 3 shelf boards
  for (let i = 0; i < 3; i++) {
    const sy = y + 22 + i * 22
    drawRect(ctx, x + 2, sy, 76, 3, '#5c4a30')
  }
  // Book spines (up to 15 across 3 rows, 5 per row)
  const bookColors = ['#3b82f6', '#10b981', '#a855f7', '#f97316', '#ef4444',
                      '#f59e0b', '#06b6d4', '#84cc16', '#ec4899', '#8b5cf6',
                      '#14b8a6', '#f43f5e', '#fb923c', '#4ade80', '#60a5fa']
  const visible = Math.min(completedCount, 15)
  for (let b = 0; b < visible; b++) {
    const row = Math.floor(b / 5)
    const col = b % 5
    const bx = x + 4 + col * 14
    const by = y + 4 + row * 22
    ctx.fillStyle = bookColors[b % bookColors.length]
    ctx.fillRect(bx, by, 11, 18)
    ctx.strokeStyle = 'rgba(0,0,0,0.4)'
    ctx.lineWidth = 0.5
    ctx.strokeRect(bx, by, 11, 18)
  }
  // Green glow when isGlowing
  if (isGlowing) {
    const glowAlpha = 0.15 + 0.1 * Math.sin(animTime / 200)
    ctx.globalAlpha = glowAlpha
    ctx.fillStyle = '#10b981'
    ctx.fillRect(x, y, 80, 80)
    ctx.globalAlpha = 1
  }
  drawText(ctx, 'ARCHIVE', x + 40, y + 90, '7px monospace', '#8b7355', 'center')
}

export function drawDeskWorkingGlow(ctx, deskX, deskY, deskW, deskH, agentColor, glowRadius) {
  const cx = deskX + deskW / 2
  const cy = deskY + deskH / 2
  const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, deskW / 2 + glowRadius)
  grad.addColorStop(0, agentColor + '40')
  grad.addColorStop(1, 'transparent')
  ctx.fillStyle = grad
  ctx.fillRect(deskX - glowRadius, deskY - glowRadius, deskW + glowRadius * 2, deskH + glowRadius * 2)
}

export function drawDeskProgressBar(ctx, deskX, deskY, deskW, elapsed, totalDuration, color) {
  const barY = deskY - 12
  const barX = deskX
  const barH = 5
  const pct = Math.min(elapsed / totalDuration, 1)
  const fillColor = pct < 0.6 ? color : pct < 0.85 ? '#fbbf24' : '#ef4444'

  // Track
  drawRect(ctx, barX, barY, deskW, barH, '#1a1a1a')
  // Fill
  if (pct > 0) drawRect(ctx, barX, barY, deskW * pct, barH, fillColor)

  // Percentage text above
  const pctLabel = `${Math.round(pct * 100)}%`
  drawText(ctx, pctLabel, deskX + deskW / 2, barY - 3, '7px monospace', fillColor, 'center')
}

export function drawCostMeter(ctx, x, y, w, h, costCurrent, costBudget, animTime = 0) {
  // Background panel
  drawRoundedRect(ctx, x - 8, y - 8, w + 16, h + 24, 4, 'rgba(0,0,0,0.75)')

  // "BUDGET" label
  drawText(ctx, 'BUDGET', x + w / 2, y - 1, '7px monospace', '#94a3b8', 'center')

  const pct = costBudget > 0 ? Math.min(costCurrent / costBudget, 1) : 0
  const fillColor = pct < 0.5 ? '#10b981' : pct < 0.8 ? '#fbbf24' : '#ef4444'

  // Track
  drawRect(ctx, x, y + 4, w, h, '#1a1a1a')

  // Fill
  if (pct > 0) drawRect(ctx, x, y + 4, w * pct, h, fillColor)

  // Tick marks at 25/50/75%
  for (const tick of [0.25, 0.5, 0.75]) {
    ctx.fillStyle = 'rgba(255,255,255,0.3)'
    ctx.fillRect(x + w * tick - 0.5, y + 4, 1, h)
  }

  // Cost label below
  drawText(ctx, `$${costCurrent.toFixed(2)} / $${costBudget}`, x + w / 2, y + h + 14, '7px monospace', fillColor, 'center')
}

export function drawStuckDeskBorder(ctx, deskX, deskY, deskW, deskH, borderAlpha) {
  ctx.globalAlpha = borderAlpha
  ctx.strokeStyle = '#ef4444'
  ctx.lineWidth = 3
  ctx.strokeRect(deskX - 1, deskY - 1, deskW + 2, deskH + 2)
  ctx.globalAlpha = 1
}

export function drawWarningTriangle(ctx, cx, y, alpha) {
  ctx.globalAlpha = alpha
  ctx.fillStyle = '#fbbf24'
  ctx.beginPath()
  ctx.moveTo(cx, y - 10)
  ctx.lineTo(cx - 8, y + 4)
  ctx.lineTo(cx + 8, y + 4)
  ctx.closePath()
  ctx.fill()
  drawText(ctx, '!', cx, y + 3, 'bold 9px monospace', '#1a1a1a', 'center')
  ctx.globalAlpha = 1
}

export function drawCompletionSparkles(ctx, cx, cy, particles) {
  for (const p of particles) {
    ctx.globalAlpha = p.alpha
    ctx.fillStyle = '#fbbf24'
    ctx.beginPath()
    ctx.arc(p.x, p.y, Math.max(0.1, p.r), 0, Math.PI * 2)
    ctx.fill()
    // Cross lines
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 0.5
    ctx.beginPath()
    ctx.moveTo(p.x - p.r * 2, p.y)
    ctx.lineTo(p.x + p.r * 2, p.y)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(p.x, p.y - p.r * 2)
    ctx.lineTo(p.x, p.y + p.r * 2)
    ctx.stroke()
  }
  ctx.globalAlpha = 1
}

// Agent name label pill above character
export function drawAgentNameLabel(ctx, cx, charY, label, agentColor) {
  const pillY = charY - 20
  const textWidth = label.length * 7
  const pillW = textWidth + 16
  const pillH = 16

  drawRoundedRect(ctx, cx - pillW / 2, pillY - pillH / 2, pillW, pillH, 4, 'rgba(0,0,0,0.75)')
  drawText(ctx, label.toUpperCase(), cx, pillY + 4, 'bold 9px monospace', '#fff', 'center')
}

// Status indicator dot
export function drawStatusDot(ctx, cx, charY, isWorking, animTime) {
  const dotX = cx + 42
  const dotY = charY - 20
  const pulse = isWorking ? 4 + Math.sin(animTime / 200) : 3
  const color = isWorking ? '#fbbf24' : '#10b981'
  drawCircle(ctx, dotX, dotY, pulse, color, 'rgba(0,0,0,0.4)', 1)
}

// Speech bubble for findings
export function drawSpeechBubble(ctx, cx, bubbleBottomY, text, agentColor) {
  const maxChars = 28
  const truncated = text.length > maxChars ? text.slice(0, maxChars) + '…' : text
  const bw = 164, bh = 44
  const bx = cx - bw / 2, by = bubbleBottomY - bh

  // Background
  drawRoundedRect(ctx, bx, by, bw, bh, 5, 'rgba(15,15,30,0.9)', agentColor, 1)

  // Tail triangle
  ctx.fillStyle = agentColor
  ctx.beginPath()
  ctx.moveTo(cx - 6, by + bh)
  ctx.lineTo(cx + 6, by + bh)
  ctx.lineTo(cx, by + bh + 8)
  ctx.closePath()
  ctx.fill()

  // Text (wrapped to 2 lines)
  ctx.font = '9px monospace'
  ctx.fillStyle = '#e2e8f0'
  ctx.textAlign = 'center'
  const line1 = truncated.slice(0, 28)
  const line2 = truncated.slice(28)
  ctx.fillText(line1, cx, by + 16)
  if (line2) ctx.fillText(line2, cx, by + 30)
}

// Importance score badge
export function drawImportanceBadge(ctx, cx, badgeY, score) {
  const color = score >= 7 ? '#10b981' : score >= 4 ? '#fbbf24' : '#ef4444'
  drawBadge(ctx, `${score}/10`, cx, badgeY, color, '#000', 4)
}

// Room decoration: central table and plants
export function drawRoomDecor(ctx) {
  // Central round table
  ctx.fillStyle = '#5c4a30'
  ctx.beginPath()
  ctx.arc(600, 260, 30, 0, Math.PI * 2)
  ctx.fill()
  ctx.strokeStyle = '#3d2f1f'
  ctx.lineWidth = 2
  ctx.stroke()

  // Plants
  drawPlant(ctx, 500, 150)
  drawPlant(ctx, 700, 150)
  drawPlant(ctx, 80, 490)
  drawPlant(ctx, 1120, 490)
  drawPlant(ctx, 600, 390)

  // Floor lamp glow
  drawCircle(ctx, 600, 500, 8, 'rgba(255,255,200,0.06)')
}

function drawPlant(ctx, x, y) {
  // Pot
  ctx.fillStyle = '#8b5e3c'
  ctx.fillRect(x - 7, y + 6, 14, 10)

  // Leaves: green circles overlapping
  ctx.fillStyle = '#2d6a2d'
  ctx.beginPath()
  ctx.arc(x, y, 10, 0, Math.PI * 2)
  ctx.fill()

  ctx.fillStyle = '#1e4a1e'
  ctx.beginPath()
  ctx.arc(x - 5, y + 4, 6, 0, Math.PI * 2)
  ctx.fill()
  ctx.beginPath()
  ctx.arc(x + 5, y + 4, 6, 0, Math.PI * 2)
  ctx.fill()
}

export function drawFloorInboxTray(ctx, x, y, stackCount, label, color) {
  // Glow halo if items present
  if (stackCount > 0) {
    ctx.globalAlpha = 0.12
    drawCircle(ctx, x + 16, y + 9, 22, '#f59e0b')
    ctx.globalAlpha = 1
  }

  // Shadow
  drawRect(ctx, x + 3, y + 3, 32, 18, 'rgba(0,0,0,0.4)')

  // Wooden base
  drawRect(ctx, x, y, 32, 18, '#8b7355', '#5c4a30', 1)

  // Stacked papers (up to 5 visible)
  const sheets = Math.min(stackCount, 5)
  for (let i = sheets - 1; i >= 0; i--) {
    ctx.globalAlpha = 0.6 + i * 0.08
    ctx.fillStyle = '#f5f5dc'
    ctx.fillRect(x + 2 + i * 0.5, y - 3 - i * 3, 28, 3)
  }
  ctx.globalAlpha = 1

  // Count badge
  if (stackCount > 0) {
    drawBadge(ctx, `${stackCount}`, x + 32, y - 4,
      stackCount > 10 ? '#ef4444' : '#374151', '#e2e8f0', 3)
  }

  // Label pill 14px above tray
  const pillW = label.length * 6 + 12
  const pillX = x + 16 - pillW / 2
  const pillY = y - 22
  drawRoundedRect(ctx, pillX, pillY, pillW, 14, 3, 'rgba(0,0,0,0.7)')
  drawText(ctx, label, x + 16, y - 12, 'bold 8px monospace', color, 'center')
}
