import { useEffect, useState } from 'react'
import FindingsFeed from './FindingsFeed'
import ExaminationsPending from './ExaminationsPending'
import AgentStatusPanel from './AgentStatusPanel'
import ActionHistory from './ActionHistory'

const API_BASE = 'http://localhost:8000/api'

export default function AgentPipeline() {
  const [findings, setFindings] = useState([])
  const [examinations, setExaminations] = useState([])
  const [agentStatus, setAgentStatus] = useState(null)
  const [actions, setActions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [findingsRes, examsRes, statusRes, actionsRes] = await Promise.all([
          fetch(`${API_BASE}/agent-pipeline/findings?importance_min=5`),
          fetch(`${API_BASE}/agent-pipeline/examinations`),
          fetch(`${API_BASE}/agent-pipeline/status`),
          fetch(`${API_BASE}/agent-pipeline/actions`)
        ])

        if (findingsRes.ok) {
          const data = await findingsRes.json()
          setFindings(Array.isArray(data) ? data : data.items || [])
        }
        if (examsRes.ok) {
          const data = await examsRes.json()
          setExaminations(Array.isArray(data) ? data : data.items || [])
        }
        if (statusRes.ok) {
          const data = await statusRes.json()
          setAgentStatus(data)
        }
        if (actionsRes.ok) {
          const data = await actionsRes.json()
          setActions(Array.isArray(data) ? data : data.items || [])
        }
        setError(null)
      } catch (err) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !findings.length && !examinations.length) {
    return (
      <div className="glass p-6">
        <div className="text-center text-gray-400">Loading agent pipeline...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ExaminationsPending examinations={examinations} />
        <AgentStatusPanel status={agentStatus} />
      </div>

      <FindingsFeed findings={findings} />

      <ActionHistory actions={actions} />

      {error && (
        <div className="glass p-4 border border-red-500 bg-red-500/10">
          <p className="text-red-400 text-sm">Error: {error}</p>
        </div>
      )}
    </div>
  )
}
