// animationUtils.js

export function getIdleBreathePulse(timeMs) {
  // Gentle 2-second cycle: 0 -> 2px -> 0
  const cycle = (timeMs % 2000) / 2000 // 0-1
  return Math.sin(cycle * Math.PI) * 2 // 0 to 2 to 0
}

export function getFadeinAlpha(timeMs, duration = 300) {
  // Fade in over duration ms
  const alpha = Math.min(1, timeMs / duration)
  return alpha
}

export function getSmoothTransition(from, to, timeMs, duration = 300) {
  // Smooth transition from one value to another
  if (timeMs >= duration) return to
  return from + (to - from) * (timeMs / duration)
}

export function getColorGlow(baseColor, isGlowing, intensity = 0.3) {
  if (!isGlowing) return baseColor
  // Brighten color for glow effect
  return lightenColor(baseColor, intensity)
}

function lightenColor(hex, percent) {
  const num = parseInt(hex.replace('#', ''), 16)
  const amt = Math.round(2.55 * percent)
  const R = Math.min(255, (num >> 16) + amt)
  const G = Math.min(255, (num >> 8 & 0x00FF) + amt)
  const B = Math.min(255, (num & 0x0000FF) + amt)
  return '#' + (0x1000000 + R * 0x10000 + G * 0x100 + B).toString(16).slice(1)
}

export function getActionFlash(timeMs, duration = 500) {
  // Brief white flash when action completes
  if (timeMs > duration) return 0
  // Flash fades out
  return 1 - (timeMs / duration)
}
