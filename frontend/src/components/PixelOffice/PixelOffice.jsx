import { useEffect, useRef, useState } from 'react'
import * as canvasHelpers from './canvasHelpers'
import * as pixelArtCharacters from './pixelArtCharacters'
import * as animationUtils from './animationUtils'

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

// Agent layout configuration
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
    let animationFrameId
    const startTime = Date.now()

    const animate = () => {
      const elapsed = Date.now() - startTime
      setAnimationState(prev => ({
        ...prev,
        time: elapsed
      }))
      animationFrameId = requestAnimationFrame(animate)
    }

    animationFrameId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationFrameId)
  }, [])

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
      const text = (finding.finding_text || '').substring(0, 40) +
                   (finding.finding_text?.length > 40 ? '...' : '')
      ctx.font = '10px Arial'
      ctx.fillStyle = canvasHelpers.Colors.text
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
  }

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
      canvasHelpers.Colors.text
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
}
