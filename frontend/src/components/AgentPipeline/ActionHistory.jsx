export default function ActionHistory({ actions }) {
  const getActionColor = (type) => {
    return type === 'autonomous'
      ? 'text-blue-300'
      : 'text-purple-300'
  }

  const getResultColor = (result) => {
    const colors = {
      success: 'text-green-400',
      failed: 'text-red-400',
      pending: 'text-yellow-400'
    }
    return colors[result] || 'text-gray-400'
  }

  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Recent Actions (24h)</h2>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {actions.length === 0 ? (
          <p className="text-gray-500 text-sm">No actions yet</p>
        ) : (
          actions.map((action) => (
            <div key={action.id} className="border border-gray-700 rounded p-2 text-xs">
              <div className="flex justify-between items-start">
                <div className="flex gap-2">
                  <span className={getActionColor(action.action_type)}>
                    {action.action_type === 'autonomous' ? '' : ''}
                    {action.action_type}
                  </span>
                  <span className={getResultColor(action.result)}>
                    {action.result}
                  </span>
                </div>
                <span className="text-gray-500">
                  {new Date(action.created_at).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
