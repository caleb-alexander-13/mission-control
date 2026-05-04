import { useState, useEffect } from 'react'

const TABS = [
  { id: 'agents', icon: '◉', label: 'Agents' },
  { id: 'metrics', icon: '#', label: 'Metrics' },
  { id: 'trading', icon: '💰', label: 'Trading' },
  { id: 'alerts', icon: '⚡', label: 'Alerts' },
]

const AGENT_COLORS = {
  sports: '#3b82f6',
  finance: '#10b981',
  creative: '#a855f7',
  tech: '#f97316',
  examination: '#f59e0b',
  executioner: '#ef4444',
}

export default function Sidebar({ collapsed, onToggle, pipelineStatus, findings, examinations, pipelineActions, activities, costs, portfolio, tradingLog }) {
  const [activeTab, setActiveTab] = useState('agents')
  const [expandedAgent, setExpandedAgent] = useState(null)
  const [findingsLog, setFindingsLog] = useState({})
  const [feedbackLoading, setFeedbackLoading] = useState({})

  const API_BASE = 'http://localhost:8000/api'

  useEffect(() => {
    // Fetch findings log for all agents
    const fetchFindingsLog = async () => {
      const agents = ['sports', 'finance', 'creative', 'tech']
      const logs = {}
      for (const agent of agents) {
        try {
          const res = await fetch(`${API_BASE}/agent-pipeline/findings-with-feedback?agent=${agent}&limit=10`)
          if (res.ok) {
            logs[agent] = await res.json()
          }
        } catch (err) {
          console.error(`Error fetching findings for ${agent}:`, err)
        }
      }
      setFindingsLog(logs)
    }
    if (activeTab === 'agents') {
      fetchFindingsLog()
    }
  }, [activeTab])

  const submitFeedback = async (findingId, feedback) => {
    setFeedbackLoading({ ...feedbackLoading, [findingId]: true })
    try {
      const res = await fetch(`${API_BASE}/agent-pipeline/findings/${findingId}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback })
      })
      if (res.ok) {
        // Update local state
        Object.keys(findingsLog).forEach(agent => {
          findingsLog[agent] = findingsLog[agent].map(f =>
            f.id === findingId ? { ...f, feedback } : f
          )
        })
        setFindingsLog({ ...findingsLog })
      }
    } catch (err) {
      console.error('Error submitting feedback:', err)
    }
    setFeedbackLoading({ ...feedbackLoading, [findingId]: false })
  }

  return (
    <aside
      className="flex flex-col h-screen border-r border-white/10 bg-gray-950 transition-all duration-200"
      style={{ width: collapsed ? 50 : 250, minWidth: collapsed ? 50 : 250 }}
    >
      {/* Header */}
      <div className="flex items-center gap-2 p-3 border-b border-white/10">
        <div className="w-6 h-6 rounded bg-green-600 flex items-center justify-center text-xs font-bold shrink-0">
          M
        </div>
        {!collapsed && <span className="text-sm font-bold tracking-wide truncate">Mission Control</span>}
      </div>

      {/* Tabs */}
      <div className="border-b border-white/10">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 w-full px-3 py-2 text-xs transition ${
              activeTab === tab.id ? 'bg-white/10 text-white' : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <span className="text-sm shrink-0">{tab.icon}</span>
            {!collapsed && <span className="truncate">{tab.label}</span>}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="overflow-y-auto flex-1" style={{ scrollbarWidth: 'thin', scrollbarColor: 'rgba(255,255,255,0.1) transparent' }}>
        {/* Agents Tab */}
        {activeTab === 'agents' && !collapsed && (
          <div>
            {Object.entries(pipelineStatus?.agents || {}).map(([name, info]) => {
              const isWorking = info.status === 'working' || info.status === 'analyzing' || info.status === 'executing'
              const pending = info.findings_pending ?? info.pending_examinations ?? info.pending_actions ?? 0
              const isExpanded = expandedAgent === name
              const agentFindings = findingsLog[name] || []

              return (
                <div key={name} className="border-b border-white/5">
                  <button
                    onClick={() => setExpandedAgent(isExpanded ? null : name)}
                    className="w-full flex items-center gap-2 px-3 py-2 hover:bg-white/5 text-left"
                  >
                    <div
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ backgroundColor: isWorking ? '#fbbf24' : '#10b981' }}
                    />
                    <span className="text-xs capitalize flex-1 font-semibold">{name}</span>
                    {pending > 0 && <span className="text-xs text-gray-500 font-semibold">{pending}</span>}
                    <span className="text-xs text-gray-600">{isExpanded ? '▼' : '▶'}</span>
                  </button>

                  {isExpanded && (
                    <div className="bg-white/5 border-t border-white/5 max-h-64 overflow-y-auto">
                      {agentFindings.length > 0 ? (
                        agentFindings.map((finding) => (
                          <div key={finding.id} className="px-3 py-2 border-b border-white/5 text-xs">
                            <div className="text-gray-300 mb-1 line-clamp-2">
                              {finding.finding_text}
                            </div>
                            <div className="text-gray-500 text-xs mb-2">
                              📌 {finding.source_name}
                            </div>
                            <div className="flex gap-2 items-center">
                              <button
                                onClick={() => submitFeedback(finding.id, 'important')}
                                disabled={feedbackLoading[finding.id]}
                                className={`px-2 py-1 rounded text-xs ${
                                  finding.feedback === 'important'
                                    ? 'bg-green-600 text-white'
                                    : 'bg-white/10 text-gray-300 hover:bg-white/20'
                                }`}
                              >
                                👍 Good
                              </button>
                              <button
                                onClick={() => submitFeedback(finding.id, 'not_important')}
                                disabled={feedbackLoading[finding.id]}
                                className={`px-2 py-1 rounded text-xs ${
                                  finding.feedback === 'not_important'
                                    ? 'bg-red-600 text-white'
                                    : 'bg-white/10 text-gray-300 hover:bg-white/20'
                                }`}
                              >
                                👎 Meh
                              </button>
                              {finding.feedback && (
                                <span className="text-xs text-gray-600 ml-auto">
                                  {finding.feedback === 'important' ? '✓' : '✗'}
                                </span>
                              )}
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="px-3 py-2 text-xs text-gray-500">
                          No findings yet
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}

        {/* Metrics Tab */}
        {activeTab === 'metrics' && !collapsed && (
          <div className="p-3 space-y-2">
            <StatCard label="Today's Findings" value={Object.keys(findings || {}).length} />
            <StatCard
              label="Pending Exams"
              value={(Array.isArray(examinations) ? examinations : []).filter(e => e.status === 'pending_action').length}
            />
            <StatCard
              label="Pending Actions"
              value={(Array.isArray(pipelineActions) ? pipelineActions : []).filter(a => a.result === 'pending').length}
            />
            <StatCard label="Total Cost" value={`$${costs?.total_cost?.toFixed(2) || '0.00'}`} />
            <StatCard
              label="Last Action"
              value={(Array.isArray(pipelineActions) ? pipelineActions : [])[0]?.result || 'none'}
            />
          </div>
        )}

        {/* Trading Tab */}
        {activeTab === 'trading' && !collapsed && (
          <div className="p-3 space-y-3">
            <div className="space-y-2">
              <StatCard label="Cash" value={`$${portfolio?.cash?.toFixed(2) || '0.00'}`} />
              <StatCard label="Total Value" value={`$${portfolio?.total_value?.toFixed(2) || '0.00'}`} />
              <StatCard
                label="P&L"
                value={`${portfolio?.pnl >= 0 ? '+' : ''}$${portfolio?.pnl?.toFixed(2) || '0.00'}`}
                color={portfolio?.pnl >= 0 ? '#10b981' : '#ef4444'}
              />
            </div>
            {tradingLog?.trades && tradingLog.trades.length > 0 && (
              <div className="border-t border-white/10 pt-2">
                <div className="text-xs text-gray-400 mb-2 font-semibold">Recent Trades</div>
                {tradingLog.trades.slice(0, 5).map((trade, i) => (
                  <div key={i} className="text-xs py-1 border-b border-white/5">
                    <div className="flex justify-between">
                      <span className="text-gray-300">{trade.action.toUpperCase()} {trade.shares.toFixed(2)} {trade.ticker}</span>
                      <span className={trade.action === 'buy' ? 'text-red-400' : 'text-green-400'}>
                        {trade.action === 'buy' ? '-' : '+'}${Math.abs(trade.cash_impact).toFixed(2)}
                      </span>
                    </div>
                    <div className="text-gray-500">@ ${trade.price.toFixed(2)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Alerts Tab */}
        {activeTab === 'alerts' && !collapsed && (
          <div>
            {(activities || []).slice(0, 5).map((item, i) => (
              <div key={i} className="px-3 py-2 border-b border-white/5 hover:bg-white/5">
                <div className="text-xs text-gray-300 truncate">{item.tool_name || item.type || 'activity'}</div>
                <div className="text-xs text-gray-500">
                  {item.created_at ? new Date(item.created_at).toLocaleTimeString() : ''}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Collapse toggle */}
      <div className="border-t border-white/10 p-2 flex justify-center">
        <button onClick={onToggle} className="text-gray-400 hover:text-white text-sm px-2 py-1">
          {collapsed ? '›' : '‹'}
        </button>
      </div>
    </aside>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div className="glass p-2 rounded">
      <div className="text-xs text-gray-400">{label}</div>
      <div className="text-sm font-bold" style={color ? { color } : {}}>{value}</div>
    </div>
  )
}
