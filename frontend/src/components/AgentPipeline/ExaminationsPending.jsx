export default function ExaminationsPending({ examinations }) {
  const getPriorityColor = (priority) => {
    const colors = {
      critical: 'text-red-400 bg-red-500/10 border-red-500',
      high: 'text-orange-400 bg-orange-500/10 border-orange-500',
      medium: 'text-yellow-400 bg-yellow-500/10 border-yellow-500',
      low: 'text-blue-400 bg-blue-500/10 border-blue-500'
    }
    return colors[priority] || 'text-gray-400'
  }

  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Pending Examinations</h2>
      <div className="space-y-2">
        {examinations.length === 0 ? (
          <p className="text-gray-500 text-sm">No pending examinations</p>
        ) : (
          examinations.map((exam) => (
            <div key={exam.id} className={`border rounded p-3 ${getPriorityColor(exam.priority)}`}>
              <p className="text-sm font-medium">{exam.finding_text.substring(0, 100)}</p>
              <p className="text-xs text-gray-400 mt-1">{exam.gameplan.substring(0, 100)}</p>
              {exam.requires_approval && (
                <div className="mt-2 flex gap-2">
                  <button className="text-xs px-2 py-1 bg-green-600 hover:bg-green-700 rounded">
                    Approve
                  </button>
                  <button className="text-xs px-2 py-1 bg-red-600 hover:bg-red-700 rounded">
                    Reject
                  </button>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
