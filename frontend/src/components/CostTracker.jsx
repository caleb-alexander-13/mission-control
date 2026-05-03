export default function CostTracker({ data }) {
  const cost = data?.total_cost || 0
  const inputTokens = data?.total_input_tokens || 0
  const outputTokens = data?.total_output_tokens || 0

  return (
    <div className="glass p-6">
      <h2 className="text-lg font-semibold mb-4">Cost Tracker</h2>
      <div className="space-y-3">
        <div className="flex justify-between items-end">
          <span className="text-gray-400">Total Cost</span>
          <span className="text-2xl font-bold">${cost.toFixed(2)}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Input Tokens</span>
          <span>{inputTokens.toLocaleString()}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Output Tokens</span>
          <span>{outputTokens.toLocaleString()}</span>
        </div>
      </div>
    </div>
  )
}
