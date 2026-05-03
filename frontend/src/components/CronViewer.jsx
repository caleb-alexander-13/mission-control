export default function CronViewer({ data }) {
  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Scheduled Jobs</h2>
      <div className="space-y-2 max-h-[300px] overflow-y-auto">
        {data && data.length > 0 ? (
          data.map((job, i) => (
            <div key={i} className="bg-black/40 rounded p-2 text-xs">
              <p className="truncate font-mono text-gray-300">{job.cron_expression}</p>
              <p className="text-gray-500 text-[10px]">{new Date(job.last_run).toLocaleString()}</p>
            </div>
          ))
        ) : (
          <p className="text-gray-500 text-sm">No scheduled jobs</p>
        )}
      </div>
    </div>
  )
}
