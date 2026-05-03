import { useEffect, useRef, useState } from 'react'

const API_BASE = 'http://localhost:8000/api'

export default function PixelOffice() {
  const canvasRef = useRef(null)
  const [status, setStatus] = useState(null)
  const [findings, setFindings] = useState({})

  // Fetch agent status and findings
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, findingsRes] = await Promise.all([
          fetch(`${API_BASE}/agent-pipeline/status`).then(r => r.json()),
          fetch(`${API_BASE}/agent-pipeline/findings?importance_min=6`).then(r => r.json())
        ])

        setStatus(statusRes)

        // Map latest finding per agent
        const latestByAgent = {}
        const findingsArray = Array.isArray(findingsRes) ? findingsRes : findingsRes.items || []
        findingsArray.forEach(f => {
          if (!latestByAgent[f.agent_name]) {
            latestByAgent[f.agent_name] = f
          }
        })
        setFindings(latestByAgent)
      } catch (err) {
        console.error('Error fetching status:', err)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  // Canvas rendering
  useEffect(() => {
    if (!canvasRef.current || !status) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const now = Date.now()

    // Set canvas size
    canvas.width = 1200
    canvas.height = 400

    // Draw background (office)
    ctx.fillStyle = '#1a1a2e'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Draw floor
    ctx.fillStyle = '#16213e'
    ctx.fillRect(0, 300, canvas.width, 100)

    // Draw grid pattern on floor
    ctx.strokeStyle = '#0f3460'
    ctx.lineWidth = 1
    for (let x = 0; x < canvas.width; x += 40) {
      ctx.beginPath()
      ctx.moveTo(x, 300)
      ctx.lineTo(x, 400)
      ctx.stroke()
    }

    // Agent positions (desk areas)
    const agents = [
      { name: 'sports', x: 100, color: '#3b82f6', label: '🏈' },
      { name: 'finance', x: 280, color: '#10b981', label: '💰' },
      { name: 'creative', x: 460, color: '#a855f7', label: '🎨' },
      { name: 'tech', x: 640, color: '#f97316', label: '⚙️' },
      { name: 'examination', x: 820, color: '#f59e0b', label: '📋' },
      { name: 'executioner', x: 1000, color: '#ef4444', label: '⚡' }
    ]

    // Draw agents at desks
    agents.forEach(agent => {
      const agentStatus = status.agents[agent.name]
      const isWorking = agentStatus?.status === 'working' || agentStatus?.status === 'analyzing' || agentStatus?.status === 'executing'

      // Draw desk
      ctx.fillStyle = '#0f3460'
      ctx.fillRect(agent.x - 40, 280, 80, 20)
      ctx.strokeStyle = agent.color
      ctx.lineWidth = 2
      ctx.strokeRect(agent.x - 40, 280, 80, 20)

      // Draw character (simple pixel)
      ctx.fillStyle = agent.color
      ctx.fillRect(agent.x - 15, 260, 30, 20) // body
      ctx.fillRect(agent.x - 10, 245, 20, 15) // head

      // Status indicator
      const pulseSize = isWorking ? 8 + Math.sin(now / 100) * 2 : 6
      ctx.fillStyle = isWorking ? '#eab308' : '#22c55e'
      ctx.beginPath()
      ctx.arc(agent.x + 20, 250, pulseSize, 0, Math.PI * 2)
      ctx.fill()

      // Agent label
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 20px Arial'
      ctx.textAlign = 'center'
      ctx.fillText(agent.label, agent.x, 320)

      // Agent name
      ctx.fillStyle = '#cbd5e1'
      ctx.font = '12px Arial'
      ctx.fillText(agent.name, agent.x, 340)

      // Status text
      if (agent.name === 'examination' || agent.name === 'executioner') {
        const pending = agent.name === 'examination'
          ? agentStatus?.pending_examinations
          : agentStatus?.pending_actions
        ctx.fillStyle = pending ? '#fca5a5' : '#86efac'
        ctx.font = '11px monospace'
        ctx.fillText(`${pending || 0} pending`, agent.x, 355)
      } else {
        ctx.fillStyle = agentStatus?.findings_pending ? '#fca5a5' : '#86efac'
        ctx.font = '11px monospace'
        ctx.fillText(`${agentStatus?.findings_pending || 0} pending`, agent.x, 355)
      }

      // Speech bubble with latest finding
      const finding = findings[agent.name]
      if (finding && isWorking) {
        const bubbleWidth = 120
        const bubbleHeight = 40
        const bubbleX = agent.x - bubbleWidth / 2
        const bubbleY = 210

        // Draw rounded rectangle (bubble)
        ctx.fillStyle = '#2d3748'
        ctx.strokeStyle = agent.color
        ctx.lineWidth = 1
        roundRect(ctx, bubbleX, bubbleY, bubbleWidth, bubbleHeight, 4)
        ctx.fill()
        ctx.stroke()

        // Draw pointer
        ctx.fillStyle = '#2d3748'
        ctx.beginPath()
        ctx.moveTo(agent.x - 5, 210)
        ctx.lineTo(agent.x + 5, 210)
        ctx.lineTo(agent.x, 200)
        ctx.fill()

        // Text in bubble
        ctx.fillStyle = '#e2e8f0'
        ctx.font = '10px Arial'
        ctx.textAlign = 'center'
        const text = finding.finding_text.substring(0, 20) + '...'
        ctx.fillText(text, agent.x, bubbleY + 20)
      }
    })

    // Draw data flow arrows
    drawArrow(ctx, 680, 270, 820, 270, '#4ade80', 'findings')
    drawArrow(ctx, 940, 270, 1000, 270, '#60a5fa', 'examinations')

  }, [status, findings])

  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Pixel Office — Agents at Work</h2>
      <canvas
        ref={canvasRef}
        className="w-full border border-gray-700 rounded bg-gray-900"
        style={{ maxWidth: '100%', height: 'auto' }}
      />
      <div className="mt-4 grid grid-cols-3 gap-4 text-xs text-gray-400">
        <div>🟢 Idle | 🟡 Working</div>
        <div>📊 Real-time status updates every 5s</div>
        <div>→ Data flows left to right</div>
      </div>
    </div>
  )
}

// Helper: Draw rounded rectangle
function roundRect(ctx, x, y, width, height, radius) {
  ctx.beginPath()
  ctx.moveTo(x + radius, y)
  ctx.lineTo(x + width - radius, y)
  ctx.arcTo(x + width, y, x + width, y + radius, radius)
  ctx.lineTo(x + width, y + height - radius)
  ctx.arcTo(x + width, y + height, x + width - radius, y + height, radius)
  ctx.lineTo(x + radius, y + height)
  ctx.arcTo(x, y + height, x, y + height - radius, radius)
  ctx.lineTo(x, y + radius)
  ctx.arcTo(x, y, x + radius, y, radius)
  ctx.closePath()
}

// Helper: Draw arrow
function drawArrow(ctx, fromX, fromY, toX, toY, color, label) {
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

  // Draw label
  ctx.fillStyle = color
  ctx.font = '10px Arial'
  ctx.textAlign = 'center'
  ctx.fillText(label, (fromX + toX) / 2, (fromY + toY) / 2 - 10)
}
