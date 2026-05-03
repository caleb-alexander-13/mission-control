import { useState, useEffect } from 'react'
import AgentStatus from './components/AgentStatus'
import ActivityFeed from './components/ActivityFeed'
import CostTracker from './components/CostTracker'
import TaskWorkshop from './components/TaskWorkshop'
import CronViewer from './components/CronViewer'
import AgentPipeline from './components/AgentPipeline/AgentPipeline'
import PixelOffice from './components/PixelOffice/PixelOffice'

const API_BASE = 'http://localhost:8000/api'

export default function App() {
  const [agentStatus, setAgentStatus] = useState(null)
  const [activities, setActivities] = useState([])
  const [costs, setCosts] = useState(null)
  const [tasks, setTasks] = useState([])
  const [crons, setCrons] = useState([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statusRes, activitiesRes, costsRes, tasksRes, cronsRes] = await Promise.all([
          fetch(`${API_BASE}/agent/status`),
          fetch(`${API_BASE}/activity/feed`),
          fetch(`${API_BASE}/cost/summary`),
          fetch(`${API_BASE}/tasks`),
          fetch(`${API_BASE}/crons`),
        ])

        if (statusRes.ok) {
          const data = await statusRes.json()
          setAgentStatus(data)
        }
        if (activitiesRes.ok) {
          const data = await activitiesRes.json()
          setActivities(data)
        }
        if (costsRes.ok) {
          const data = await costsRes.json()
          setCosts(data)
        }
        if (tasksRes.ok) {
          const data = await tasksRes.json()
          setTasks(Array.isArray(data) ? data : data.items || [])
        }
        if (cronsRes.ok) {
          const data = await cronsRes.json()
          setCrons(Array.isArray(data) ? data : data.items || [])
        }
      } catch (err) {
        console.error('Fetch error:', err)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-black p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
          Mission Control
        </h1>
        <p className="text-gray-400 mb-8">AI Agent Activity Dashboard</p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <AgentStatus data={agentStatus} />
          <CostTracker data={costs} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ActivityFeed data={activities} />
          </div>
          <div className="flex flex-col gap-6">
            <CronViewer data={crons} />
          </div>
        </div>

        <div className="mt-6">
          <TaskWorkshop data={tasks} />
        </div>

        <div className="mt-6">
          <PixelOffice />
        </div>

        <div className="mt-6">
          <AgentPipeline />
        </div>
      </div>
    </div>
  )
}
