import { useState, useEffect } from 'react'

const TABS = [
  { id: 'agents', icon: '◉', label: 'Agents' },
  { id: 'metrics', icon: '#', label: 'Metrics' },
  { id: 'trading', icon: '💰', label: 'Trading' },
  { id: 'finance', icon: '$', label: 'Finance' },
  { id: 'articles', icon: '📰', label: 'Articles' },
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
  const [articleDrafts, setArticleDrafts] = useState([])
  const [draftApproving, setDraftApproving] = useState({})
  const [costSummary, setCostSummary] = useState(null)
  const [tradeReasons, setTradeReasons] = useState({}) // ticker -> reason map
  const [tradeFindings, setTradeFindings] = useState([]) // trades with their findings
  const [tradingTab, setTradingTab] = useState('holdings') // 'holdings' or 'history'

  const API_BASE = 'http://localhost:8000/api'

  useEffect(() => {
    if (activeTab === 'agents') {
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
      fetchFindingsLog()
    } else if (activeTab === 'articles') {
      // Fetch article drafts
      const fetchArticles = async () => {
        try {
          const res = await fetch(`${API_BASE}/agent-pipeline/article-drafts`)
          if (res.ok) {
            const data = await res.json()
            setArticleDrafts(data.drafts || [])
          }
        } catch (err) {
          console.error('Error fetching articles:', err)
        }
      }
      fetchArticles()
    } else if (activeTab === 'finance') {
      // Fetch cost summary
      const fetchCosts = async () => {
        try {
          const res = await fetch(`${API_BASE}/cost/summary`)
          if (res.ok) {
            setCostSummary(await res.json())
          }
        } catch (err) {
          console.error('Error fetching costs:', err)
        }
      }
      fetchCosts()
    } else if (activeTab === 'trading') {
      // Fetch portfolio with trade reasons
      const fetchPortfolioData = async () => {
        try {
          const res = await fetch(`${API_BASE}/portfolio`)
          if (res.ok) {
            const data = await res.json()
            setTradeFindings(data.recent_trades || [])
          }
        } catch (err) {
          console.error('Error fetching portfolio data:', err)
        }
      }
      fetchPortfolioData()
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
        // Remove finding from list after feedback submitted
        const updated = { ...findingsLog }
        Object.keys(updated).forEach(agent => {
          updated[agent] = updated[agent].filter(f => f.id !== findingId)
        })
        setFindingsLog(updated)
      }
    } catch (err) {
      console.error('Error submitting feedback:', err)
    }
    setFeedbackLoading({ ...feedbackLoading, [findingId]: false })
  }

  const approveDraft = async (draftId) => {
    setDraftApproving({ ...draftApproving, [draftId]: true })
    try {
      const res = await fetch(`${API_BASE}/agent-pipeline/article-drafts/${draftId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      if (res.ok) {
        // Remove from drafts list
        setArticleDrafts(articleDrafts.filter(d => d.id !== draftId))
      }
    } catch (err) {
      console.error('Error approving draft:', err)
    }
    setDraftApproving({ ...draftApproving, [draftId]: false })
  }

  const rejectDraft = async (draftId, feedback = '') => {
    setDraftApproving({ ...draftApproving, [draftId]: true })
    try {
      const res = await fetch(`${API_BASE}/agent-pipeline/article-drafts/${draftId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback })
      })
      if (res.ok) {
        // Remove from drafts list
        setArticleDrafts(articleDrafts.filter(d => d.id !== draftId))
      }
    } catch (err) {
      console.error('Error rejecting draft:', err)
    }
    setDraftApproving({ ...draftApproving, [draftId]: false })
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
              const agentFindings = (findingsLog[name] || []).filter(f => !f.feedback)

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
          <div className="flex flex-col h-full">
            {/* Summary Cards */}
            <div className="p-3 space-y-2 border-b border-white/10">
              <StatCard label="Cash" value={`$${portfolio?.cash?.toFixed(2) || '0.00'}`} />
              <StatCard label="Total Value" value={`$${portfolio?.total_value?.toFixed(2) || '0.00'}`} />
              <StatCard
                label="P&L"
                value={`${portfolio?.pnl >= 0 ? '+' : ''}$${portfolio?.pnl?.toFixed(2) || '0.00'}`}
                color={portfolio?.pnl >= 0 ? '#10b981' : '#ef4444'}
              />
            </div>

            {/* Sub-tabs */}
            <div className="flex border-b border-white/10">
              <button
                onClick={() => setTradingTab('holdings')}
                className={`flex-1 px-3 py-2 text-xs font-semibold transition ${
                  tradingTab === 'holdings'
                    ? 'bg-white/10 text-white border-b-2 border-blue-500'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Holdings ({portfolio?.holdings?.length || 0})
              </button>
              <button
                onClick={() => setTradingTab('history')}
                className={`flex-1 px-3 py-2 text-xs font-semibold transition ${
                  tradingTab === 'history'
                    ? 'bg-white/10 text-white border-b-2 border-blue-500'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                History
              </button>
              <button
                onClick={() => setTradingTab('performance')}
                className={`flex-1 px-3 py-2 text-xs font-semibold transition ${
                  tradingTab === 'performance'
                    ? 'bg-white/10 text-white border-b-2 border-blue-500'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Stats
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {tradingTab === 'holdings' && (
                <>
                  {portfolio?.holdings && portfolio.holdings.length > 0 ? (
                    portfolio.holdings.map((holding, i) => {
                      const buyTrade = tradeFindings.find(t => t.ticker === holding.ticker && t.action === 'buy')
                      return (
                        <div key={i} className="border border-blue-900/50 rounded p-2 bg-blue-950/20 space-y-2">
                          <div className="flex justify-between items-start">
                            <div>
                              <div className="text-sm font-bold text-blue-100">{holding.ticker}</div>
                              <div className="text-xs text-gray-400 mt-1">
                                {holding.shares?.toFixed(2)} shares @ ${holding.avg_cost?.toFixed(2)}
                              </div>
                            </div>
                            <span className={`text-sm font-semibold ${holding.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {holding.unrealized_pnl >= 0 ? '+' : ''}${holding.unrealized_pnl?.toFixed(2)}
                            </span>
                          </div>

                          {/* Current price and value */}
                          <div className="text-xs text-gray-500">
                            Now: ${holding.current_price?.toFixed(2)} · Value: ${holding.market_value?.toFixed(2)}
                          </div>

                          {/* Why we bought it */}
                          {buyTrade?.reason && (
                            <div className="border-t border-blue-900/30 pt-2">
                              <div className="text-xs text-green-300 font-semibold mb-1">💡 Why we own this</div>
                              <div className="text-xs text-gray-300">{buyTrade.reason}</div>
                            </div>
                          )}
                        </div>
                      )
                    })
                  ) : (
                    <div className="text-xs text-gray-500 text-center py-8">No holdings yet</div>
                  )}
                </>
              )}

              {tradingTab === 'history' && (
                <>
                  {tradeFindings && tradeFindings.length > 0 ? (
                    tradeFindings.slice(0, 10).map((trade, i) => (
                      <div key={i} className="border border-white/10 rounded p-2 bg-white/5 space-y-2">
                        {/* Trade Action */}
                        <div className="flex justify-between items-start">
                          <div>
                            <span className="text-sm font-bold">{trade.action.toUpperCase()}</span>
                            <div className="text-xs text-gray-400 mt-0.5">
                              {trade.shares?.toFixed(2)} shares of {trade.ticker} @ ${trade.price?.toFixed(2)}
                            </div>
                          </div>
                          <span className={`text-sm font-semibold ${trade.action === 'buy' ? 'text-red-400' : 'text-green-400'}`}>
                            {trade.action === 'buy' ? '-' : '+'}${Math.abs(trade.cash_impact)?.toFixed(2)}
                          </span>
                        </div>

                        {/* News that triggered the trade */}
                        {trade.finding_text && (
                          <div className="text-xs text-gray-500 italic line-clamp-2 mt-1 border-t border-white/5 pt-1">
                            "{trade.finding_text.slice(0, 90)}..."
                          </div>
                        )}
                        {trade.confidence && (
                          <div className="text-xs text-gray-400">
                            Confidence: {trade.confidence}/10 · Source: {trade.source_name}
                          </div>
                        )}

                        {/* Reason/Analysis */}
                        {trade.reason && (
                          <div className="border-t border-white/5 pt-2">
                            <div className="text-xs text-green-300 font-semibold mb-1">💡 Why this trade</div>
                            <div className="text-xs text-gray-300">{trade.reason}</div>
                          </div>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-gray-500 text-center py-8">No trades yet</div>
                  )}
                </>
              )}

              {tradingTab === 'performance' && portfolio?.performance && (
                <div className="p-3 space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { label: 'Win Rate', value: `${portfolio.performance.win_rate}%`, color: 'text-green-400' },
                      { label: 'Total Trades', value: portfolio.performance.total_trades, color: 'text-white' },
                      { label: 'Best Trade', value: `+$${portfolio.performance.best_trade}`, color: 'text-green-400' },
                      { label: 'Worst Trade', value: `$${portfolio.performance.worst_trade}`, color: 'text-red-400' },
                    ].map(({ label, value, color }) => (
                      <div key={label} className="border border-white/10 rounded p-2 text-center">
                        <div className={`text-lg font-bold ${color}`}>{value}</div>
                        <div className="text-xs text-gray-500">{label}</div>
                      </div>
                    ))}
                  </div>
                  <div className="text-xs text-gray-500 text-center">
                    {portfolio.performance.wins}W / {portfolio.performance.losses}L · Avg ${portfolio.performance.avg_size}/trade
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Articles Tab */}
        {activeTab === 'articles' && !collapsed && (
          <div className="flex flex-col h-full">
            {/* Sub-tabs */}
            <div className="flex border-b border-white/10">
              <div className="px-3 py-2 text-xs font-semibold text-gray-300">
                Drafts ({articleDrafts.length})
              </div>
            </div>

            {/* Drafts */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
              {articleDrafts.length > 0 ? (
                articleDrafts.map((draft) => (
                  <div key={draft.id} className="border border-white/10 rounded p-2 bg-white/5 space-y-2">
                    <div className="text-sm font-semibold text-gray-100 line-clamp-2">{draft.title}</div>
                    <div className="text-xs text-gray-400 line-clamp-3">{draft.content}</div>
                    <div className="flex gap-2 items-center">
                      <button
                        onClick={() => approveDraft(draft.id)}
                        disabled={draftApproving[draft.id]}
                        className="px-2 py-1 rounded text-xs bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
                      >
                        ✓ Publish to GMSeat
                      </button>
                      <button
                        onClick={() => rejectDraft(draft.id, 'Needs revision')}
                        disabled={draftApproving[draft.id]}
                        className="px-2 py-1 rounded text-xs bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
                      >
                        ✗ Reject
                      </button>
                    </div>
                    <div className="text-xs text-gray-500">Topic: {draft.topic}</div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-gray-500 text-center py-8">No drafts pending approval</div>
              )}
            </div>
          </div>
        )}

        {/* Finance Tab */}
        {activeTab === 'finance' && !collapsed && (
          <div className="flex flex-col h-full">
            {/* Budget gauge */}
            <div className="p-3 border-b border-white/10">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-400">Daily Budget</span>
                <span className="text-white font-mono">${costSummary?.today?.total_estimated_usd?.toFixed(4) ?? '0.0000'} / $100</span>
              </div>
              <div className="h-1.5 bg-white/10 rounded">
                <div className="h-1.5 bg-green-500 rounded transition-all"
                  style={{ width: `${Math.min((costSummary?.today?.total_estimated_usd ?? 0), 100)}%` }} />
              </div>
            </div>
            {/* Period rows */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {[
                { label: 'Last Hour', key: 'last_hour', prev: null },
                { label: 'Today', key: 'today', prev: 'yesterday' },
                { label: 'Yesterday', key: 'yesterday', prev: null },
                { label: 'This Week', key: 'this_week', prev: null },
                { label: 'All Time', key: 'all_time', prev: null },
              ].map(({ label, key, prev }) => {
                const period = costSummary?.[key]
                const prevPeriod = prev ? costSummary?.[prev] : null
                const total = period?.total_estimated_usd ?? 0
                const delta = prevPeriod ? total - prevPeriod.total_estimated_usd : null
                const ac = period?.agent_costs
                return (
                  <div key={key} className="border border-white/10 rounded p-2 bg-white/5">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-semibold text-gray-300">{label}</span>
                      <div className="flex items-center gap-2">
                        {delta !== null && (
                          <span className={`text-xs ${delta >= 0 ? 'text-red-400' : 'text-green-400'}`}>
                            {delta >= 0 ? '+' : ''}{delta.toFixed(4)}
                          </span>
                        )}
                        <span className="text-sm font-mono text-white">${total.toFixed(4)}</span>
                      </div>
                    </div>
                    {ac && (
                      <div className="text-xs text-gray-500 space-y-0.5">
                        <div className="flex justify-between">
                          <span>Findings ({ac.findings ? Math.round(ac.findings / 0.002) : 0})</span>
                          <span>${(ac.findings ?? 0).toFixed(4)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Examinations ({ac.examinations ? Math.round(ac.examinations / 0.008) : 0})</span>
                          <span>${(ac.examinations ?? 0).toFixed(4)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Trades ({ac.trades ? Math.round(ac.trades / 0.001) : 0})</span>
                          <span>${(ac.trades ?? 0).toFixed(4)}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
              {/* Burn rate footer */}
              {costSummary?.this_week && (
                <div className="border border-white/10 rounded p-2 bg-white/5 text-xs text-gray-400 space-y-1">
                  <div className="flex justify-between">
                    <span>Burn Rate</span>
                    <span className="text-white">${((costSummary.this_week.total_estimated_usd ?? 0) / 7).toFixed(2)}/day</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Budget Remaining</span>
                    <span className="text-green-400">${(100 - (costSummary.today?.total_estimated_usd ?? 0)).toFixed(2)}</span>
                  </div>
                </div>
              )}
            </div>
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
