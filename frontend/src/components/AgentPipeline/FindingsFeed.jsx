export default function FindingsFeed({ findings }) {
  const getAgentColor = (agent) => {
    const colors = {
      sports: 'bg-blue-500/20 border-blue-500 text-blue-300',
      finance: 'bg-green-500/20 border-green-500 text-green-300',
      creative: 'bg-purple-500/20 border-purple-500 text-purple-300',
      tech: 'bg-orange-500/20 border-orange-500 text-orange-300'
    }
    return colors[agent] || 'bg-gray-500/20 border-gray-500 text-gray-300'
  }

  const getImportanceColor = (score) => {
    if (score >= 8) return 'text-red-400 font-bold'
    if (score >= 6) return 'text-orange-400'
    if (score >= 4) return 'text-yellow-400'
    return 'text-gray-400'
  }

  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Live Findings Feed</h2>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {findings.length === 0 ? (
          <p className="text-gray-500 text-sm">No findings yet. Agents are researching...</p>
        ) : (
          findings.map((finding) => (
            <div key={finding.id} className="border border-gray-700 rounded p-3 hover:border-gray-500 transition">
              <div className="flex items-start justify-between gap-2 mb-2">
                <span className={`px-2 py-1 rounded text-xs border ${getAgentColor(finding.agent_name)}`}>
                  {finding.agent_name.toUpperCase()}
                </span>
                <span className={`text-sm font-semibold ${getImportanceColor(finding.importance_score)}`}>
                  {finding.importance_score}/10
                </span>
              </div>
              <p className="text-sm text-gray-300 mb-1">{finding.finding_text.substring(0, 120)}</p>
              <div className="flex gap-2 text-xs text-gray-500">
                <span>{finding.category}</span>
                <span>•</span>
                <span>{finding.source_name}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
