export default function AgentStatusPanel({ status }) {
  if (!status) return null

  const getStatusIndicator = (agentStatus) => {
    return agentStatus === 'idle'
      ? 'w-2 h-2 rounded-full bg-green-500'
      : 'w-2 h-2 rounded-full bg-yellow-500 animate-pulse'
  }

  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Pipeline Status</h2>
      <div className="space-y-3 text-sm">
        {Object.entries(status.agents || {}).map(([agent, info]) => (
          <div key={agent} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={getStatusIndicator(info.status)}></div>
              <span className="capitalize font-medium">{agent}</span>
            </div>
            <div className="text-xs text-gray-400">
              {agent === 'examination' || agent === 'executioner' ? (
                <span>
                  {agent === 'examination'
                    ? `${info.pending_examinations || 0} pending`
                    : `${info.pending_actions || 0} pending`}
                </span>
              ) : (
                <span>{info.findings_pending || 0} pending</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
