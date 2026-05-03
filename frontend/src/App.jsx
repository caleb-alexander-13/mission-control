import { useState, useEffect, useRef } from 'react'
import Sidebar from './components/Sidebar'
import PixelOffice from './components/PixelOffice/PixelOffice'

const API_BASE = 'http://localhost:8000/api'

const THRESHOLD_COLORS = { 10: '#10b981', 25: '#fbbf24', 50: '#f97316', 75: '#ef4444' }
const THRESHOLD_LABELS = { 10: '10%', 25: '25%', 50: '50%', 75: '75%' }

function CostAlertToast({ alerts, onDismiss }) {
  useEffect(() => {
    if (alerts.length === 0) return
    const t = setTimeout(onDismiss, 6000)
    return () => clearTimeout(t)
  }, [alerts, onDismiss])

  if (alerts.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {alerts.map(pct => (
        <div
          key={pct}
          className="flex items-center gap-3 px-4 py-3 rounded-xl shadow-xl pointer-events-auto"
          style={{ background: 'rgba(10,10,20,0.95)', border: `1px solid ${THRESHOLD_COLORS[pct]}`, minWidth: 240 }}
        >
          <span style={{ color: THRESHOLD_COLORS[pct], fontSize: 20 }}>⚡</span>
          <div>
            <div className="text-white font-bold text-sm" style={{ fontFamily: 'monospace' }}>
              BUDGET ALERT — {THRESHOLD_LABELS[pct]}
            </div>
            <div className="text-gray-300 text-xs" style={{ fontFamily: 'monospace' }}>
              Daily spend crossed ${100 * pct / 100} threshold
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function App() {
  const [pipelineStatus, setPipelineStatus] = useState(null)
  const [findings, setFindings] = useState({})
  const [examinations, setExaminations] = useState([])
  const [pipelineActions, setPipelineActions] = useState([])
  const [activities, setActivities] = useState([])
  const [costs, setCosts] = useState(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [pendingAlerts, setPendingAlerts] = useState([])
  const shownAlertsRef = useRef(new Set())

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [pipelineRes, findingsRes, examsRes, actionsRes, activitiesRes, costsRes] = await Promise.all([
          fetch(`${API_BASE}/agent-pipeline/status`),
          fetch(`${API_BASE}/agent-pipeline/findings?importance_min=6`),
          fetch(`${API_BASE}/agent-pipeline/examinations`),
          fetch(`${API_BASE}/agent-pipeline/actions`),
          fetch(`${API_BASE}/activity/feed`),
          fetch(`${API_BASE}/cost/summary`),
        ])

        if (pipelineRes.ok) {
          const data = await pipelineRes.json()
          setPipelineStatus(data)
        }
        if (findingsRes.ok) {
          const data = await findingsRes.json()
          const findingsArray = Array.isArray(data) ? data : data.items || []
          const latestByAgent = {}
          findingsArray.forEach(f => {
            if (!latestByAgent[f.agent_name]) {
              latestByAgent[f.agent_name] = f
            }
          })
          setFindings(latestByAgent)
        }
        if (examsRes.ok) {
          const data = await examsRes.json()
          setExaminations(Array.isArray(data) ? data : data.items || [])
        }
        if (actionsRes.ok) {
          const data = await actionsRes.json()
          setPipelineActions(Array.isArray(data) ? data : data.items || [])
        }
        if (activitiesRes.ok) {
          const data = await activitiesRes.json()
          setActivities(data)
        }
        if (costsRes.ok) {
          const data = await costsRes.json()
          setCosts(data)
        }

        // Check cost thresholds
        try {
          const alertRes = await fetch(`${API_BASE}/cost/alert-check`)
          if (alertRes.ok) {
            const alertData = await alertRes.json()
            const newAlerts = (alertData.newly_triggered || []).filter(
              pct => !shownAlertsRef.current.has(pct)
            )
            if (newAlerts.length > 0) {
              newAlerts.forEach(pct => shownAlertsRef.current.add(pct))
              setPendingAlerts(newAlerts)
            }
          }
        } catch (_) { /* alert check is best-effort */ }
      } catch (err) {
        console.error('Fetch error:', err)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="flex flex-row h-screen overflow-hidden bg-gray-950">
      <CostAlertToast alerts={pendingAlerts} onDismiss={() => setPendingAlerts([])} />
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(p => !p)}
        pipelineStatus={pipelineStatus}
        findings={findings}
        examinations={examinations}
        pipelineActions={pipelineActions}
        activities={activities}
        costs={costs}
      />
      <div className="flex-1 h-screen overflow-hidden flex items-center justify-center">
        <PixelOffice
          pipelineStatus={pipelineStatus}
          findings={findings}
          examinations={examinations}
          pipelineActions={pipelineActions}
          costs={costs}
        />
      </div>
    </div>
  )
}
