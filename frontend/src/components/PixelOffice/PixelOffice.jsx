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
