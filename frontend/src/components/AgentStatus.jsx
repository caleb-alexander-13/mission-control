export default function AgentStatus({ data }) {
  const isIdle = data?.status === 'idle'
  const statusColor = isIdle ? 'bg-green-500' : 'bg-yellow-500'
  const statusText = isIdle ? 'Idle' : 'Working'
  const lastToolTime = data?.last_tool_at ? new Date(data.last_tool_at).toLocaleTimeString() : 'Never'

  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Agent Status</h2>
      <div className="flex items-center gap-3 mb-4">
        <div className={`w-3 h-3 rounded-full ${statusColor} animate-pulse`} />
        <span className="text-sm font-medium">{statusText}</span>
      </div>

      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">Session</span>
          <code className="text-gray-300 text-xs">{data?.current_session_id?.slice(0, 8)}...</code>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Project</span>
          <code className="text-gray-300 text-xs truncate">{data?.current_project}</code>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Last Tool</span>
          <span className="text-gray-300">{data?.last_tool || 'None'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Last Activity</span>
          <span className="text-gray-300 text-xs">{lastToolTime}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Sessions</span>
          <span className="text-gray-300">{data?.active_sessions_count || 0}</span>
        </div>
      </div>
    </div>
  )
}
