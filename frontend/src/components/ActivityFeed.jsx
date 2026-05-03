export default function ActivityFeed({ data }) {
  const items = data?.items || data || []

  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Activity Feed</h2>
      <div className="text-gray-400 text-sm max-h-96 overflow-y-auto">
        {items.length > 0 ? (
          <div className="space-y-2">
            {items.slice(0, 10).map((item, i) => (
              <div key={i} className="flex justify-between items-center py-1 border-b border-gray-800">
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-gray-800 px-2 py-1 rounded">{item.type}</span>
                  <span>{item.tool_name || item.path?.split('/').pop() || 'File'}</span>
                </div>
                <span className="text-xs text-gray-500">{new Date(item.created_at).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        ) : (
          <p>No recent activity</p>
        )}
      </div>
    </div>
  )
}
