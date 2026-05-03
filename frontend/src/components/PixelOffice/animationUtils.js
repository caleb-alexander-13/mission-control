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

export const SPARKLE_DURATION = 900

export function getSparkleParticles(cx, cy, completionAge) {
  if (completionAge < 0 || completionAge > SPARKLE_DURATION) return []
  const t = completionAge / SPARKLE_DURATION
  const alpha = 1 - t
  return [0,1,2,3,4,5,6,7].map(i => {
    const angle = (i / 8) * Math.PI * 2 + t * 0.8
    const dist = 14 + t * 28
    return {
      x: cx + Math.cos(angle) * dist,
      y: cy + Math.sin(angle) * dist,
      alpha: alpha * (0.6 + 0.4 * Math.sin(i + t * 10)),
      r: 2 - t * 1.5,
    }
  })
}

export function getWorkingGlowRadius(animTime) {
  return 6 + Math.sin(animTime / 600) * 6
}

export function getStuckWarningAlpha(animTime) {
  return 0.5 + 0.5 * Math.sin(animTime / 250)
}

export function getStuckBorderAlpha(animTime) {
  return Math.max(0, Math.sin(animTime / 330))
}
