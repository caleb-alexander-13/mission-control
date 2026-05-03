// pixelArtCharacters.js

import { drawRect, Colors } from './canvasHelpers'

/**
 * Draw a detailed & shaded pixel character (60x80px) for R&D agents
 * Characters have: head, body, arms, legs, held object
 */
export function drawRDAgentCharacter(ctx, agent, x, y) {
  const agentColor = Colors.agent[agent] || Colors.agent.tech
  if (!Colors.agent[agent]) {
    console.warn(`Unknown agent type: ${agent}, using tech as fallback`)
  }

  // Head with shading
  drawRect(ctx, x + 8, y + 2, 9, 8, '#fdbf69')    // main
  drawRect(ctx, x + 9, y + 3, 7, 6, '#f5a623')    // shading

  // Eyes
  drawRect(ctx, x + 10, y + 4, 2, 2, '#ffffff')   // white left
  drawRect(ctx, x + 11, y + 4, 1, 2, '#000')      // pupil left
  drawRect(ctx, x + 14, y + 4, 2, 2, '#ffffff')   // white right
  drawRect(ctx, x + 15, y + 4, 1, 2, '#000')      // pupil right

  // Mouth
  drawRect(ctx, x + 11, y + 7, 3, 1, '#000')

  // Shirt
  drawRect(ctx, x + 9, y + 10, 7, 7, agentColor)        // main color
  drawRect(ctx, x + 10, y + 11, 5, 5, shadeColor(agentColor)) // shading

  // Arms
  drawRect(ctx, x + 6, y + 12, 2, 8, '#fdbf69')   // left
  drawRect(ctx, x + 17, y + 12, 2, 8, '#fdbf69')  // right

  // Hands
  drawRect(ctx, x + 5, y + 20, 1, 1, '#fdbf69')   // left hand
  drawRect(ctx, x + 20, y + 20, 1, 1, '#fdbf69')  // right hand

  // Legs
  drawRect(ctx, x + 10, y + 17, 2, 10, shadeColor(agentColor)) // left
  drawRect(ctx, x + 13, y + 17, 2, 10, shadeColor(agentColor)) // right

  // Shoes
  drawRect(ctx, x + 9, y + 27, 3, 1, '#000')      // left
  drawRect(ctx, x + 13, y + 27, 3, 1, '#000')     // right
}

/**
 * Draw held object based on agent type
 */
export function drawHeldObject(ctx, agent, x, y) {
  switch (agent) {
    case 'sports':
      drawFootball(ctx, x + 19, y + 13)
      break
    case 'finance':
      drawMoneyBag(ctx, x + 18, y + 7)
      break
    case 'creative':
      drawPaintbrush(ctx, x + 22, y + 6)
      break
    case 'tech':
      drawGear(ctx, x + 20, y + 2)
      break
    default:
      console.warn(`Unknown agent type for held object: ${agent}`)
  }
}

function drawFootball(ctx, x, y) {
  drawRect(ctx, x, y, 4, 2, '#92400e')  // brown
  drawRect(ctx, x + 1, y + 1, 2, 0.5, '#ffffff') // white stripe
}

function drawMoneyBag(ctx, x, y) {
  drawRect(ctx, x, y, 4, 5, '#10b981')   // bag
  drawRect(ctx, x + 1, y + 1, 2, 2, '#fbbf24') // $ area
}

function drawPaintbrush(ctx, x, y) {
  drawRect(ctx, x, y, 1, 7, '#8b5a2b')  // handle
  drawRect(ctx, x - 1, y - 1, 3, 2, '#ec4899') // bristles
}

function drawGear(ctx, x, y) {
  drawRect(ctx, x, y, 4, 4, '#64748b')  // center
  drawRect(ctx, x - 1, y + 1, 1, 2, '#64748b') // tooth
  drawRect(ctx, x + 4, y + 1, 1, 2, '#64748b') // tooth
  drawRect(ctx, x + 1, y - 1, 2, 1, '#64748b') // tooth
  drawRect(ctx, x + 1, y + 4, 2, 1, '#64748b') // tooth
}

/**
 * Draw Examination Agent (larger, at desk with papers)
 */
export function drawExaminationAgent(ctx, x, y) {
  // Head
  drawRect(ctx, x + 15, y + 2, 9, 8, '#fdbf69')
  drawRect(ctx, x + 16, y + 3, 7, 6, '#f5a623')
  drawRect(ctx, x + 17, y + 4, 2, 2, '#ffffff')
  drawRect(ctx, x + 18, y + 4, 1, 2, '#000')
  drawRect(ctx, x + 21, y + 4, 2, 2, '#ffffff')
  drawRect(ctx, x + 22, y + 4, 1, 2, '#000')
  drawRect(ctx, x + 18, y + 7, 3, 1, '#000')

  // Body (analyst shirt)
  drawRect(ctx, x + 16, y + 10, 7, 7, '#6366f1')
  drawRect(ctx, x + 17, y + 11, 5, 5, '#4f46e5')

  // Arms
  drawRect(ctx, x + 13, y + 12, 2, 8, '#fdbf69')
  drawRect(ctx, x + 24, y + 12, 2, 8, '#fdbf69')

  // Legs
  drawRect(ctx, x + 17, y + 17, 2, 10, '#1e3a8a')
  drawRect(ctx, x + 20, y + 17, 2, 10, '#1e3a8a')

  // Shoes
  drawRect(ctx, x + 16, y + 27, 3, 1, '#000')
  drawRect(ctx, x + 20, y + 27, 3, 1, '#000')

  // Desk
  drawRect(ctx, x + 5, y + 30, 50, 3, '#8b6f47')
}

/**
 * Draw Executioner Agent (at desk, ready for action)
 */
export function drawExecutionerAgent(ctx, x, y) {

  // Head
  drawRect(ctx, x + 15, y + 2, 9, 8, '#fdbf69')
  drawRect(ctx, x + 16, y + 3, 7, 6, '#f5a623')
  drawRect(ctx, x + 17, y + 4, 2, 2, '#ffffff')
  drawRect(ctx, x + 18, y + 4, 1, 2, '#000')
  drawRect(ctx, x + 21, y + 4, 2, 2, '#ffffff')
  drawRect(ctx, x + 22, y + 4, 1, 2, '#000')
  drawRect(ctx, x + 18, y + 7, 3, 1, '#fbbf24') // alert mouth

  // Body (action shirt, red accent)
  drawRect(ctx, x + 16, y + 10, 7, 7, '#dc2626')
  drawRect(ctx, x + 17, y + 11, 5, 5, '#991b1b')

  // Arms
  drawRect(ctx, x + 13, y + 12, 2, 8, '#fdbf69')
  drawRect(ctx, x + 24, y + 12, 2, 8, '#fdbf69')

  // Legs
  drawRect(ctx, x + 17, y + 17, 2, 10, '#7f1d1d')
  drawRect(ctx, x + 20, y + 17, 2, 10, '#7f1d1d')

  // Shoes
  drawRect(ctx, x + 16, y + 27, 3, 1, '#000')
  drawRect(ctx, x + 20, y + 27, 3, 1, '#000')

  // Desk
  drawRect(ctx, x + 5, y + 30, 50, 3, '#8b6f47')
}

// Helper to shade a color
function shadeColor(color) {
  const shadeMap = {
    '#3b82f6': '#1e40af', // sports
    '#10b981': '#059669', // finance
    '#a855f7': '#7c3aed', // creative
    '#f97316': '#ea580c'  // tech
  }
  return shadeMap[color] || color
}
