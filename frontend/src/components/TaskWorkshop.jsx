export default function TaskWorkshop({ data }) {
  const columns = {
    pending: data?.filter(t => t.status === 'pending') || [],
    in_progress: data?.filter(t => t.status === 'in_progress') || [],
    completed: data?.filter(t => t.status === 'completed') || [],
  }

  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Task Workshop</h2>
      <div className="grid grid-cols-3 gap-4">
        {Object.entries(columns).map(([status, tasks]) => (
          <div key={status} className="bg-black/40 rounded-lg p-4">
            <h3 className="text-sm font-semibold text-gray-300 mb-3 capitalize">{status.replace('_', ' ')}</h3>
            <div className="space-y-2 min-h-[100px]">
              {tasks.length > 0 ? (
                tasks.map(task => (
                  <div key={task.id} className="bg-gray-800/60 rounded p-2 text-xs">
                    <p className="truncate">{task.subject}</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-xs">No tasks</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
