import { useSession } from '../context/SessionContext'

/**
 * Build overall and per-domain score breakdowns from the session feedback.
 * Only answered exercises count toward totals.
 */
export function computeResults(exercises, feedback) {
  let correct = 0
  let answered = 0
  const byDomain = {}

  for (const ex of exercises) {
    const result = feedback[ex.exerciseId]
    if (!result) continue
    answered += 1
    const bucket = byDomain[ex.domain] || { correct: 0, total: 0 }
    bucket.total += 1
    if (result.correct) {
      correct += 1
      bucket.correct += 1
    }
    byDomain[ex.domain] = bucket
  }

  return { correct, answered, total: exercises.length, byDomain }
}

export default function Summary() {
  const { exercises, feedback, reset } = useSession()
  const { correct, total, byDomain } = computeResults(exercises, feedback)
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Session complete</h2>

      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6 text-center">
        <p className="text-5xl font-bold text-databricks-500">
          {correct}/{total}
        </p>
        <p className="text-gray-600 mt-2">{pct}% correct</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">By domain</h3>
        <ul className="space-y-2">
          {Object.entries(byDomain).map(([domain, stats]) => (
            <li key={domain} className="flex justify-between text-gray-800">
              <span>{domain}</span>
              <span className="font-medium">
                {stats.correct}/{stats.total}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <button
        type="button"
        onClick={reset}
        className="w-full bg-databricks-500 hover:bg-databricks-600 text-white font-medium py-2.5 rounded transition-colors"
      >
        Start a new session
      </button>
    </div>
  )
}
