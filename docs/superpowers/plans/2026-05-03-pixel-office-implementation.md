# Pixel Office Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real-time canvas-based pixel art office visualization showing the agent pipeline (2×2 R&D grid + Examination + Executioner agents) with detailed & shaded characters, rich data display, and subtle animations.

**Architecture:** React component (PixelOffice.jsx) uses canvas for rendering. Data flows from backend APIs (5s poll) → component state → canvas drawing functions. Helper modules handle character rendering, animations, and canvas utilities. Canvas dimensions 1000×800px, responsive scaling.

**Tech Stack:** React (hooks), HTML5 Canvas, JavaScript (ES6+), existing backend APIs (/agent-pipeline/*), no external dependencies.

---

## File Structure

**Files to create:**
- `frontend/src/components/PixelOffice/pixelArtCharacters.js` — Functions for drawing detailed & shaded pixel characters
- `frontend/src/components/PixelOffice/canvasHelpers.js` — Utility functions for canvas drawing (rectangles, text, colors, etc.)
- `frontend/src/components/PixelOffice/animationUtils.js` — Animation state and timing utilities

**Files to modify:**
- `frontend/src/components/PixelOffice/PixelOffice.jsx` — Main component (refactor layout, integrate new helpers)

---

## Task Breakdown

### Task 1: Set Up Canvas, Layout, and Data Fetching

**Files:**
- Modify: `frontend/src/components/PixelOffice/PixelOffice.jsx:1-100`

**Goals:** Refactor PixelOffice to use new 2×2 grid layout (1000×800px canvas), fetch all required data (status, findings, examinations, actions), manage animation state.

- [ ] **Step 1: Update canvas dimensions and layout constants**

Replace the existing useEffect with proper layout setup:

```javascript
import { useEffect, useRef, useState } from 'react'

const API_BASE = 'http://localhost:8000/api'

// Layout constants
const CANVAS_WIDTH = 1000
const CANVAS_HEIGHT = 800
const GRID_PADDING = 20
const AGENT_CARD_WIDTH = (CANVAS_WIDTH - GRID_PADDING * 3) / 2  // 490px
const AGENT_CARD_HEIGHT = 280
const EXAMINATION_HEIGHT = 160
const EXECUTIONER_HEIGHT = 160
const FLOOR_Y = AGENT_CARD_HEIGHT * 2 + GRID_PADDING * 2

export default function PixelOffice() {
  const canvasRef = useRef(null)
  const [data, setData] = useState({
    status: null,
    findings: {},
    examinations: null,
    actions: null
  })
  const [animationState, setAnimationState] = useState({
    time: 0,
    agents: {}
  })

  // Fetch all required data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, findingsRes, examsRes, actionsRes] = await Promise.all([
          fetch(`${API_BASE}/agent-pipeline/status`).then(r => r.json()),
          fetch(`${API_BASE}/agent-pipeline/findings?importance_min=6`).then(r => r.json()),
          fetch(`${API_BASE}/agent-pipeline/examinations`).then(r => r.json()),
          fetch(`${API_BASE}/agent-pipeline/actions`).then(r => r.json())
        ])

        // Map latest finding per agent
        const latestByAgent = {}
        const findingsArray = Array.isArray(findingsRes) ? findingsRes : findingsRes.items || []
        findingsArray.forEach(f => {
          if (!latestByAgent[f.agent_name]) {
            latestByAgent[f.agent_name] = f
          }
        })

        setData({
          status: statusRes || {},
          findings: latestByAgent,
          examinations: Array.isArray(examsRes) ? examsRes : examsRes?.items || [],
          actions: Array.isArray(actionsRes) ? actionsRes : actionsRes?.items || []
        })
      } catch (err) {
        console.error('Error fetching agent pipeline data:', err)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  // Animation loop
  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    canvas.width = CANVAS_WIDTH
    canvas.height = CANVAS_HEIGHT

    let animationId
    let startTime = Date.now()

    const animate = () => {
      const now = Date.now()
      const elapsed = now - startTime

      setAnimationState(prev => ({
        ...prev,
        time: elapsed
      }))

      // Render will happen in next effect
      animationId = requestAnimationFrame(animate)
    }

    animationId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationId)
  }, [])
```

- [ ] **Step 2: Create agent layout configuration**

Add a helper to define agent positions:

```javascript
const AGENTS_RD = [
  { id: 'sports', name: 'sports', label: '⚽', color: '#3b82f6', x: GRID_PADDING, y: GRID_PADDING },
  { id: 'finance', name: 'finance', label: '💰', color: '#10b981', x: GRID_PADDING + AGENT_CARD_WIDTH + GRID_PADDING, y: GRID_PADDING },
  { id: 'creative', name: 'creative', label: '🎨', color: '#a855f7', x: GRID_PADDING, y: GRID_PADDING + AGENT_CARD_HEIGHT + GRID_PADDING },
  { id: 'tech', name: 'tech', label: '⚙️', color: '#f97316', x: GRID_PADDING + AGENT_CARD_WIDTH + GRID_PADDING, y: GRID_PADDING + AGENT_CARD_HEIGHT + GRID_PADDING }
]

const EXAMINATION_AGENT = {
  id: 'examination',
  name: 'examination',
  label: '📋',
  color: '#f59e0b',
  x: GRID_PADDING,
  y: FLOOR_Y + GRID_PADDING,
  width: CANVAS_WIDTH - GRID_PADDING * 2
}

const EXECUTIONER_AGENT = {
  id: 'executioner',
  name: 'executioner',
  label: '⚡',
  color: '#ef4444',
  x: GRID_PADDING,
  y: FLOOR_Y + GRID_PADDING + EXAMINATION_HEIGHT + GRID_PADDING,
  width: CANVAS_WIDTH - GRID_PADDING * 2
}
```

- [ ] **Step 3: Return basic JSX structure**

```javascript
  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Pixel Office — Agents at Work</h2>
      <canvas
        ref={canvasRef}
        className="w-full border border-gray-700 rounded bg-gray-900"
        style={{ maxWidth: '100%', height: 'auto', imageRendering: 'pixelated' }}
      />
      <div className="mt-4 grid grid-cols-3 gap-4 text-xs text-gray-400">
        <div>🟢 Idle | 🟡 Working</div>
        <div>📊 Real-time status updates every 5s</div>
        <div>→ Data flows: Research → Analysis → Action</div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run and verify canvas renders**

```bash
cd /Users/calebaalexander/Desktop/mission-control/frontend
npm run dev
```

Open http://localhost:5173 and verify a blank 1000×800px canvas appears. No errors in console.

- [ ] **Step 5: Commit**

```bash
cd /Users/calebaalexander/Desktop/mission-control
git add frontend/src/components/PixelOffice/PixelOffice.jsx
git commit -m "feat: set up canvas layout and data fetching

- Refactor to 1000x800px canvas with 2x2 grid + 2 large agents
- Fetch from all 4 API endpoints (status, findings, examinations, actions)
- Set up animation loop with requestAnimationFrame
- Define agent layout constants and positions
- No rendering yet, just infrastructure"
```

---

### Task 2: Create Canvas Helper Utilities

**Files:**
- Create: `frontend/src/components/PixelOffice/canvasHelpers.js`

**Goals:** Reusable functions for drawing on canvas (colors, rectangles, rounded rectangles, text, circles).

- [ ] **Step 1: Create canvasHelpers.js with utility functions**

```javascript
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
  ctx.fillStyle = '#000'
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
```

- [ ] **Step 2: Run and verify no errors**

```bash
cd /Users/calebaalexander/Desktop/mission-control/frontend
npm run dev
```

Check console for any import errors. PixelOffice should still render blank canvas.

- [ ] **Step 3: Commit**

```bash
cd /Users/calebaalexander/Desktop/mission-control
git add frontend/src/components/PixelOffice/canvasHelpers.js
git commit -m "feat: add canvas drawing utility functions

- Colors object for consistent color scheme
- Functions: drawRect, drawRoundedRect, drawCircle, drawText, drawBadge, drawLine, drawArrow
- Helper functions: getImportanceColor, getImportanceLabel"
```

---

### Task 3: Create Detailed & Shaded Pixel Character Renderer

**Files:**
- Create: `frontend/src/components/PixelOffice/pixelArtCharacters.js`

**Goals:** Functions to draw detailed & shaded pixel art characters for each agent type.

- [ ] **Step 1: Create base character drawing function**

```javascript
// pixelArtCharacters.js

import { drawRect, Colors } from './canvasHelpers'

/**
 * Draw a detailed & shaded pixel character (60x80px) for R&D agents
 * Characters have: head, body, arms, legs, held object
 */
export function drawRDAgentCharacter(ctx, agent, x, y) {
  const agentColor = Colors.agent[agent]
  
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
  const w = 60
  const h = 80
  
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
  drawRect(ctx, x + 5, y + 30, w - 10, 3, '#8b6f47')
}

/**
 * Draw Executioner Agent (at desk, ready for action)
 */
export function drawExecutionerAgent(ctx, x, y) {
  const w = 60
  const h = 80
  
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
  drawRect(ctx, x + 5, y + 30, w - 10, 3, '#8b6f47')
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
```

- [ ] **Step 2: Verify no errors**

```bash
cd /Users/calebaalexander/Desktop/mission-control/frontend
npm run dev
```

- [ ] **Step 3: Commit**

```bash
cd /Users/calebaalexander/Desktop/mission-control
git add frontend/src/components/PixelOffice/pixelArtCharacters.js
git commit -m "feat: add detailed & shaded pixel character renderers

- drawRDAgentCharacter: 60x80px R&D agent with head, body, arms, legs
- drawHeldObject: agent-specific objects (football, money, brush, gear)
- drawExaminationAgent: analyst character at desk
- drawExecutionerAgent: action character at desk
- Includes clothing detail and shading for depth"
```

---

### Task 4: Draw Static Office Layout

**Files:**
- Modify: `frontend/src/components/PixelOffice/PixelOffice.jsx:100-200`

**Goals:** Render office background, grid, agent cards with borders, Examination/Executioner areas.

- [ ] **Step 1: Add drawing function for static layout**

Add this function to PixelOffice.jsx:

```javascript
function drawOfficeLayout(ctx) {
  const { Colors } = canvasHelpers

  // Background
  ctx.fillStyle = Colors.background
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)

  // Grid floor pattern on agent card area
  ctx.strokeStyle = Colors.gridLine
  ctx.lineWidth = 1
  for (let x = 0; x < CANVAS_WIDTH; x += 40) {
    ctx.beginPath()
    ctx.moveTo(x, FLOOR_Y)
    ctx.lineTo(x, FLOOR_Y + EXAMINATION_HEIGHT + EXECUTIONER_HEIGHT + GRID_PADDING * 2)
    ctx.stroke()
  }

  // Draw R&D agent card backgrounds
  AGENTS_RD.forEach(agent => {
    canvasHelpers.drawRoundedRect(
      ctx,
      agent.x,
      agent.y,
      AGENT_CARD_WIDTH,
      AGENT_CARD_HEIGHT,
      4,
      Colors.card,
      agent.color,
      2
    )
  })

  // Draw Examination card background
  canvasHelpers.drawRoundedRect(
    ctx,
    EXAMINATION_AGENT.x,
    EXAMINATION_AGENT.y,
    EXAMINATION_AGENT.width,
    EXAMINATION_HEIGHT,
    4,
    Colors.card,
    EXAMINATION_AGENT.color,
    2
  )

  // Draw Executioner card background
  canvasHelpers.drawRoundedRect(
    ctx,
    EXECUTIONER_AGENT.x,
    EXECUTIONER_AGENT.y,
    EXECUTIONER_AGENT.width,
    EXECUTIONER_HEIGHT,
    4,
    Colors.card,
    EXECUTIONER_AGENT.color,
    2
  )
}
```

- [ ] **Step 2: Import canvasHelpers at top of PixelOffice.jsx**

```javascript
import { useEffect, useRef, useState } from 'react'
import * as canvasHelpers from './canvasHelpers'
```

- [ ] **Step 3: Add rendering in canvas effect**

Replace the animation effect's render section:

```javascript
  // Canvas rendering
  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    canvas.width = CANVAS_WIDTH
    canvas.height = CANVAS_HEIGHT

    // Draw static layout
    drawOfficeLayout(ctx)

    // TODO: Draw agents and data in next tasks
  }, [data, animationState])
```

- [ ] **Step 4: Test rendering**

```bash
cd /Users/calebaalexander/Desktop/mission-control/frontend
npm run dev
```

You should see the office layout with 6 card areas (2×2 grid + 2 large areas below). Colors match the design.

- [ ] **Step 5: Commit**

```bash
cd /Users/calebaalexander/Desktop/mission-control
git add frontend/src/components/PixelOffice/PixelOffice.jsx
git commit -m "feat: draw static office layout

- Office background with floor grid pattern
- 4 R&D agent cards in 2x2 grid with color-coded borders
- Examination agent card (full width)
- Executioner agent card (full width)
- All cards have rounded corners and proper spacing"
```

---

### Task 5: Draw R&D Agent Cards with Data

**Files:**
- Modify: `frontend/src/components/PixelOffice/PixelOffice.jsx:200-300`

**Goals:** Render character, importance score, category badge, latest finding, pending count for each R&D agent.

- [ ] **Step 1: Create function to draw R&D agent card content**

Add to PixelOffice.jsx:

```javascript
function drawRDAgentCard(ctx, agent, agentStatus, finding, animationTime) {
  const cardX = agent.x
  const cardY = agent.y
  const centerX = cardX + AGENT_CARD_WIDTH / 2
  const centerY = cardY + AGENT_CARD_HEIGHT / 2

  // Draw character
  pixelArtCharacters.drawRDAgentCharacter(ctx, agent.name, centerX - 30, cardY + 20)
  pixelArtCharacters.drawHeldObject(ctx, agent.name, centerX - 30, cardY + 20)

  // Draw importance score (if finding exists)
  if (finding) {
    const scoreColor = canvasHelpers.getImportanceColor(finding.importance_score)
    canvasHelpers.drawText(
      ctx,
      `${finding.importance_score}/10`,
      centerX,
      cardY + 15,
      'bold 14px Arial',
      scoreColor
    )

    // Draw category badge
    canvasHelpers.drawBadge(
      ctx,
      finding.category || 'unknown',
      centerX,
      cardY + AGENT_CARD_HEIGHT - 30,
      '#4b5563',
      '#e2e8f0'
    )

    // Draw finding text in speech bubble
    const bubbleX = centerX
    const bubbleY = cardY + AGENT_CARD_HEIGHT - 50
    const bubbleW = AGENT_CARD_WIDTH - 20
    const bubbleH = 35
    canvasHelpers.drawRoundedRect(
      ctx,
      bubbleX - bubbleW / 2,
      bubbleY - bubbleH / 2,
      bubbleW,
      bubbleH,
      3,
      '#1a1a2e',
      agent.color,
      1
    )

    // Finding text (truncate to fit)
    const text = finding.finding_text.substring(0, 40) + (finding.finding_text.length > 40 ? '...' : '')
    ctx.font = '10px Arial'
    ctx.fillStyle = Colors.text
    ctx.textAlign = 'center'
    ctx.fillText(text, bubbleX, bubbleY + 2)
  }

  // Draw pending count
  const pendingCount = agentStatus?.findings_pending || 0
  const pendingColor = pendingCount > 0 ? '#fbbf24' : '#10b981'
  canvasHelpers.drawText(
    ctx,
    `${pendingCount} pending`,
    centerX,
    cardY + AGENT_CARD_HEIGHT - 10,
    '10px monospace',
    pendingColor,
    'center'
  )

  // Draw status indicator (pulse animation)
  const isWorking = agentStatus?.status === 'working'
  const pulseSize = isWorking ? 4 + Math.sin(animationTime / 200) * 1 : 3
  const indicatorColor = isWorking ? '#fbbf24' : '#10b981'
  canvasHelpers.drawCircle(
    ctx,
    centerX + 20,
    cardY + 25,
    pulseSize,
    indicatorColor
  )
}
```

- [ ] **Step 2: Import pixelArtCharacters**

Add at top of PixelOffice.jsx:

```javascript
import * as pixelArtCharacters from './pixelArtCharacters'
import * as canvasHelpers from './canvasHelpers'
```

- [ ] **Step 3: Update render function to call drawRDAgentCard**

Modify the canvas rendering effect:

```javascript
  // Canvas rendering
  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    canvas.width = CANVAS_WIDTH
    canvas.height = CANVAS_HEIGHT

    // Draw static layout
    drawOfficeLayout(ctx)

    // Draw R&D agents with data
    AGENTS_RD.forEach(agent => {
      const agentStatus = data.status?.agents?.[agent.name]
      const finding = data.findings?.[agent.name]
      drawRDAgentCard(ctx, agent, agentStatus, finding, animationState.time)
    })
  }, [data, animationState])
```

- [ ] **Step 4: Test rendering**

```bash
cd /Users/calebaalexander/Desktop/mission-control/frontend
npm run dev
```

You should see pixel characters, importance scores (colored), category badges, finding text in bubbles, and pending counts for each R&D agent.

- [ ] **Step 5: Commit**

```bash
cd /Users/calebaalexander/Desktop/mission-control
git add frontend/src/components/PixelOffice/PixelOffice.jsx
git commit -m "feat: render R&D agent cards with data

- Draw pixel characters for each R&D agent
- Display importance score (color-coded 1-10)
- Show category badge (injury, market_movement, etc.)
- Latest finding text in speech bubble
- Pending count with status indicator
- Idle/working status pulse animation"
```

---

### Task 6: Draw Examination and Executioner Agents

**Files:**
- Modify: `frontend/src/components/PixelOffice/PixelOffice.jsx:300-400`

**Goals:** Render Examination agent (with pending count and papers animation) and Executioner agent (with status and action display).

- [ ] **Step 1: Create function to draw Examination agent**

Add to PixelOffice.jsx:

```javascript
function drawExaminationAgent(ctx, examsCount, animationTime) {
  const x = EXAMINATION_AGENT.x
  const y = EXAMINATION_AGENT.y
  const centerX = x + EXAMINATION_AGENT.width / 2

  // Draw character
  pixelArtCharacters.drawExaminationAgent(ctx, centerX - 30, y + 15)

  // Draw status text
  const isAnalyzing = examsCount > 0
  const statusColor = isAnalyzing ? '#fbbf24' : '#10b981'
  const statusText = isAnalyzing ? `Analyzing ${examsCount} findings...` : 'Idle'

  canvasHelpers.drawText(
    ctx,
    statusText,
    centerX + 40,
    y + 30,
    'bold 14px Arial',
    statusColor
  )

  // Draw pending count (bold)
  canvasHelpers.drawText(
    ctx,
    `${examsCount} pending examinations`,
    centerX + 40,
    y + 50,
    '12px monospace',
    Colors.text
  )

  // Draw animated papers stacking (visual queue metaphor)
  const paperStackHeight = Math.min(examsCount * 2, 20) // max 20px
  const paperY = y + 90 - paperStackHeight
  for (let i = 0; i < Math.min(examsCount, 10); i++) {
    const offset = (animationTime / 50 + i) % 3 // slow drift
    canvasHelpers.drawRect(
      ctx,
      centerX - 15,
      paperY + i * 2 + offset,
      30,
      1,
      '#cbd5e1',
      '#64748b',
      0.5
    )
  }
}
```

- [ ] **Step 2: Create function to draw Executioner agent**

Add to PixelOffice.jsx:

```javascript
function drawExecutionerAgent(ctx, actionsCount, animationTime) {
  const x = EXECUTIONER_AGENT.x
  const y = EXECUTIONER_AGENT.y
  const centerX = x + EXECUTIONER_AGENT.width / 2

  // Draw character
  pixelArtCharacters.drawExecutionerAgent(ctx, centerX - 30, y + 15)

  // Determine status
  let statusText = 'Idle'
  let statusColor = '#10b981'

  if (actionsCount > 0) {
    statusText = `${actionsCount} pending actions`
    statusColor = '#fbbf24'
  }

  // Draw status text
  canvasHelpers.drawText(
    ctx,
    statusText,
    centerX + 40,
    y + 30,
    'bold 14px Arial',
    statusColor
  )

  // Draw execution detail
  const recentAction = data.actions?.[0]
  if (recentAction) {
    const resultColor = recentAction.result === 'success' ? '#10b981' : 
                       recentAction.result === 'pending' ? '#fbbf24' : '#ef4444'
    canvasHelpers.drawText(
      ctx,
      `Last: ${recentAction.result}`,
      centerX + 40,
      y + 50,
      '11px monospace',
      resultColor
    )
  }

  // Draw SMS indicator if awaiting approval
  if (actionsCount > 0) {
    canvasHelpers.drawText(
      ctx,
      '📱 awaiting approval',
      centerX + 40,
      y + 70,
      '10px monospace',
      '#60a5fa'
    )
  }
}
```

- [ ] **Step 3: Update render function to call these**

Modify the canvas rendering effect:

```javascript
  // Canvas rendering
  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    canvas.width = CANVAS_WIDTH
    canvas.height = CANVAS_HEIGHT

    // Draw static layout
    drawOfficeLayout(ctx)

    // Draw R&D agents with data
    AGENTS_RD.forEach(agent => {
      const agentStatus = data.status?.agents?.[agent.name]
      const finding = data.findings?.[agent.name]
      drawRDAgentCard(ctx, agent, agentStatus, finding, animationState.time)
    })

    // Draw Examination agent
    const examCount = data.examinations?.filter(e => e.status === 'pending_action').length || 0
    drawExaminationAgent(ctx, examCount, animationState.time)

    // Draw Executioner agent
    const actionCount = data.actions?.filter(a => a.result === 'pending').length || 0
    drawExecutionerAgent(ctx, actionCount, animationState.time)
  }, [data, animationState])
```

- [ ] **Step 4: Test rendering**

```bash
cd /Users/calebaalexander/Desktop/mission-control/frontend
npm run dev
```

You should see Examination and Executioner agents with status text, pending counts, and animated papers.

- [ ] **Step 5: Commit**

```bash
cd /Users/calebaalexander/Desktop/mission-control
git add frontend/src/components/PixelOffice/PixelOffice.jsx
git commit -m "feat: render Examination and Executioner agents

- Draw Examination agent character at desk
- Display pending examination count with analyzing status
- Animate paper stacking as visual queue metaphor
- Draw Executioner agent character at desk
- Show pending action count and last action result
- SMS indicator when awaiting user approvals"
```

---

### Task 7: Implement Subtle Animations

**Files:**
- Create: `frontend/src/components/PixelOffice/animationUtils.js`
- Modify: `frontend/src/components/PixelOffice/PixelOffice.jsx:400-500`

**Goals:** Implement idle breathing, finding fade-in, color transitions, and smooth data updates.

- [ ] **Step 1: Create animationUtils.js**

```javascript
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
```

- [ ] **Step 2: Update status indicator animation in drawRDAgentCard**

Modify the status indicator drawing to use animations:

```javascript
  // Draw status indicator with breathing animation
  const isWorking = agentStatus?.status === 'working'
  const breathe = isWorking ? 0 : animationUtils.getIdleBreathePulse(animationTime)
  const pulseSize = isWorking ? 5 + Math.sin(animationTime / 150) : 3 + breathe
  const indicatorColor = isWorking ? '#fbbf24' : '#10b981'
  
  canvasHelpers.drawCircle(
    ctx,
    centerX + 20,
    cardY + 25,
    pulseSize,
    indicatorColor
  )
```

- [ ] **Step 3: Add finding fade-in animation**

Modify drawRDAgentCard to fade in findings:

```javascript
    // Finding text in speech bubble (with fade-in)
    const bubbleX = centerX
    const bubbleY = cardY + AGENT_CARD_HEIGHT - 50
    const bubbleW = AGENT_CARD_WIDTH - 20
    const bubbleH = 35
    
    const fadeAlpha = animationUtils.getFadeinAlpha(animationTime)
    ctx.globalAlpha = fadeAlpha
    
    canvasHelpers.drawRoundedRect(
      ctx,
      bubbleX - bubbleW / 2,
      bubbleY - bubbleH / 2,
      bubbleW,
      bubbleH,
      3,
      '#1a1a2e',
      agent.color,
      1
    )

    // Finding text
    const text = finding.finding_text.substring(0, 40) + (finding.finding_text.length > 40 ? '...' : '')
    ctx.font = '10px Arial'
    ctx.fillStyle = Colors.text
    ctx.textAlign = 'center'
    ctx.fillText(text, bubbleX, bubbleY + 2)
    
    ctx.globalAlpha = 1 // reset
```

- [ ] **Step 4: Add paper stacking animation to Examination agent**

Already implemented in Task 6 with slow drift. Verify it works.

- [ ] **Step 5: Import animationUtils in PixelOffice.jsx**

```javascript
import * as animationUtils from './animationUtils'
```

- [ ] **Step 6: Test animations**

```bash
cd /Users/calebaalexander/Desktop/mission-control/frontend
npm run dev
```

Observe:
- Status indicators pulsing when agents are idle (gentle 2-second breathing)
- Findings fading in smoothly
- Papers drifting slowly on Examination agent

- [ ] **Step 7: Commit**

```bash
cd /Users/calebaalexander/Desktop/mission-control
git add frontend/src/components/PixelOffice/animationUtils.js
git commit -m "feat: implement subtle animations

- Idle breathing: gentle pulse on status indicator (2s cycle)
- Finding fade-in: smooth 300ms fade when data arrives
- Color transitions: smooth interpolation for color changes
- Paper stacking: slow vertical drift on Examination agent
- Action flash: brief white flash on completion"
```

---

### Task 8: Polish and Testing

**Files:**
- Modify: `frontend/src/components/PixelOffice/PixelOffice.jsx`

**Goals:** Handle edge cases, responsive sizing, error states, performance optimization.

- [ ] **Step 1: Add responsive canvas scaling**

Modify PixelOffice.jsx return statement:

```javascript
  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Pixel Office — Agent Pipeline</h2>
      <div className="w-full bg-gray-900 rounded border border-gray-700 overflow-hidden">
        <canvas
          ref={canvasRef}
          className="w-full block"
          style={{ 
            maxWidth: '100%', 
            height: 'auto',
            display: 'block',
            imageRendering: 'pixelated'
          }}
        />
      </div>
      <div className="mt-4 grid grid-cols-3 gap-4 text-xs text-gray-400">
        <div>🟢 Idle | 🟡 Working</div>
        <div>📊 Updates every 5s</div>
        <div>→ Research → Analysis → Action</div>
      </div>
    </div>
  )
```

- [ ] **Step 2: Add empty state handling**

Modify drawOfficeLayout to show loading message if no data:

```javascript
function drawOfficeLayout(ctx) {
  // ... existing code ...
  
  // Show loading message if no data
  if (!data.status || !Object.keys(data.findings).length) {
    ctx.font = '14px Arial'
    ctx.fillStyle = Colors.textMuted
    ctx.textAlign = 'center'
    ctx.fillText('Loading agent data...', CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2)
  }
}
```

- [ ] **Step 3: Add error handling for missing data**

Wrap data access in safe getters:

```javascript
const safeGetFinding = (agent) => data.findings?.[agent] || null
const safeGetStatus = (agent) => data.status?.agents?.[agent] || { status: 'idle', findings_pending: 0 }
const safeGetExamCount = () => data.examinations?.filter(e => e.status === 'pending_action').length || 0
const safeGetActionCount = () => data.actions?.filter(a => a.result === 'pending').length || 0
```

- [ ] **Step 4: Optimize rendering (cancel previous frame if updating)**

Update the render effect to use a flag:

```javascript
  useEffect(() => {
    if (!canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    canvas.width = CANVAS_WIDTH
    canvas.height = CANVAS_HEIGHT

    // Draw all layers
    drawOfficeLayout(ctx)

    AGENTS_RD.forEach(agent => {
      const agentStatus = safeGetStatus(agent.name)
      const finding = safeGetFinding(agent.name)
      drawRDAgentCard(ctx, agent, agentStatus, finding, animationState.time)
    })

    const examCount = safeGetExamCount()
    drawExaminationAgent(ctx, examCount, animationState.time)

    const actionCount = safeGetActionCount()
    drawExecutionerAgent(ctx, actionCount, animationState.time)
  }, [data, animationState])
```

- [ ] **Step 5: Test with real data**

```bash
cd /Users/calebaalexander/Desktop/mission-control/frontend
npm run dev
```

Open http://localhost:5173, navigate to the agent pipeline section. Verify:
- Data loads within 5 seconds
- Animations are smooth and subtle
- All agent cards display correctly
- Responsive sizing works on different screen sizes

- [ ] **Step 6: Manual testing checklist**

Test these scenarios:
- [ ] No data initially, shows "Loading..." 
- [ ] Data arrives and renders correctly
- [ ] Status pulses when agent is working
- [ ] Finding text fades in smoothly
- [ ] Pending counts update when data changes
- [ ] Examination papers animate
- [ ] No console errors

- [ ] **Step 7: Commit final polish**

```bash
cd /Users/calebaalexander/Desktop/mission-control
git add frontend/src/components/PixelOffice/PixelOffice.jsx
git commit -m "feat: polish and edge case handling

- Responsive canvas scaling for different screen sizes
- Empty state: show loading message if no data
- Safe data getters to handle missing fields
- Optimize rendering with conditional checks
- Clean up unused code from old implementation"
```

---

## Summary

All tasks complete. The Pixel Office visualization now:
- ✅ Displays 2×2 R&D agents + Examination + Executioner
- ✅ Renders detailed & shaded pixel characters
- ✅ Shows importance scores, categories, findings, pending counts
- ✅ Polls backend APIs every 5 seconds
- ✅ Implements subtle animations (breathing, fading, drifting)
- ✅ Handles edge cases and responsive sizing
- ✅ Ready for integration into Mission Control dashboard

