// canvasHelpers.js

export const Colors = {
  // Importance scores
  importance: {
    low: '#ef4444',    // red 1-3
    medium: '#fbbf24', // yellow 4-6
    high: '#10b981'    // green 7-10
  },
  // Agent body colors
  agent: {
    sports: '#3b82f6',    // blue
    finance: '#10b981',   // green
    creative: '#a855f7',  // purple
    tech: '#f97316'       // orange
  },
  // Status colors
  status: {
    idle: '#10b981',      // green
    working: '#fbbf24',   // yellow
    error: '#ef4444'      // red
  },
  // Background
  background: '#1a1a2e',
  floor: '#16213e',
  gridLine: '#0f3460',
  card: '#2d3748',
  text: '#e2e8f0',
  textMuted: '#cbd5e1'
}

export function drawRect(ctx, x, y, w, h, fillColor, strokeColor = null, strokeWidth = 1) {
  ctx.fillStyle = fillColor
  ctx.fillRect(x, y, w, h)
  if (strokeColor) {
    ctx.strokeStyle = strokeColor
    ctx.lineWidth = strokeWidth
    ctx.strokeRect(x, y, w, h)
  }
}

export function drawRoundedRect(ctx, x, y, w, h, radius, fillColor, strokeColor = null, strokeWidth = 1) {
  ctx.fillStyle = fillColor
  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.lineTo(x + w - radius, y)
  ctx.arcTo(x + w, y, x + w, y + radius, radius)
  ctx.lineTo(x + w, y + h - radius)
  ctx.arcTo(x + w, y + h, x + w - radius, y + h, radius)
  ctx.lineTo(x + radius, y + h)
  ctx.arcTo(x, y + h, x, y + h - radius, radius)
  ctx.lineTo(x, y + radius)
  ctx.arcTo(x, y, x + radius, y, radius)
  ctx.closePath()
  ctx.fill()

  if (strokeColor) {
    ctx.strokeStyle = strokeColor
    ctx.lineWidth = strokeWidth
    ctx.stroke()
  }
}

export function drawCircle(ctx, x, y, radius, fillColor, strokeColor = null, strokeWidth = 1) {
  ctx.fillStyle = fillColor
  ctx.beginPath()
  ctx.arc(x, y, radius, 0, Math.PI * 2)
  ctx.fill()

  if (strokeColor) {
    ctx.strokeStyle = strokeColor
    ctx.lineWidth = strokeWidth
    ctx.stroke()
  }
}

export function drawText(ctx, text, x, y, font = '12px Arial', color = Colors.text, align = 'left') {
  ctx.font = font
  ctx.fillStyle = color
  ctx.textAlign = align
  ctx.fillText(text, x, y)
}

export function drawBadge(ctx, text, x, y, bgColor, textColor = '#000', padding = 4) {
  ctx.font = '10px monospace'
  const metrics = ctx.measureText(text)
  const width = metrics.width + padding * 2
  const height = 14 + padding * 2

  drawRoundedRect(ctx, x - width / 2, y - height / 2, width, height, 2, bgColor)
  drawText(ctx, text, x, y + 3, '10px monospace', textColor, 'center')
}

export function drawLine(ctx, x1, y1, x2, y2, color = Colors.textMuted, width = 1) {
  ctx.strokeStyle = color
  ctx.lineWidth = width
  ctx.beginPath()
  ctx.moveTo(x1, y1)
  ctx.lineTo(x2, y2)
  ctx.stroke()
}

export function drawArrow(ctx, fromX, fromY, toX, toY, color = '#4ade80') {
  const headlen = 15
  const angle = Math.atan2(toY - fromY, toX - fromX)

  // Draw line
  ctx.strokeStyle = color
  ctx.lineWidth = 2
  ctx.beginPath()
  ctx.moveTo(fromX, fromY)
  ctx.lineTo(toX, toY)
  ctx.stroke()

  // Draw arrowhead
  ctx.fillStyle = color
  ctx.beginPath()
  ctx.moveTo(toX, toY)
  ctx.lineTo(toX - headlen * Math.cos(angle - Math.PI / 6), toY - headlen * Math.sin(angle - Math.PI / 6))
  ctx.lineTo(toX - headlen * Math.cos(angle + Math.PI / 6), toY - headlen * Math.sin(angle + Math.PI / 6))
  ctx.closePath()
  ctx.fill()
}

export function getImportanceColor(score) {
  if (score <= 3) return Colors.importance.low
  if (score <= 6) return Colors.importance.medium
  return Colors.importance.high
}

export function getImportanceLabel(score) {
  if (score <= 3) return 'Low'
  if (score <= 6) return 'Medium'
  return 'High'
}
