import { useState } from 'react'
import { useSession } from '../context/SessionContext'
import { fetchExercises } from '../api'
import { DOMAINS, DIFFICULTIES } from '../constants'

/**
 * Landing page: pick filters and start a practice session.
 */
export default function SessionSelect() {
  const { startSession } = useSession()
  const [domain, setDomain] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleStart() {
    setLoading(true)
    setError(null)
    try {
      const exercises = await fetchExercises({
        domain: domain || undefined,
        difficulty: difficulty || undefined,
      })
      if (!exercises || exercises.length === 0) {
        setError('No exercises match those filters. Try broadening your selection.')
        return
      }
      startSession(exercises)
    } catch (e) {
      setError(e.message || 'Failed to load exercises. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">Start a practice session</h2>

      <div className="space-y-5 bg-white border border-gray-200 rounded-lg p-6">
        <div>
          <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-1">
            Domain
          </label>
          <select
            id="domain"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-databricks-500"
          >
            <option value="">All domains</option>
            {DOMAINS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700 mb-1">
            Difficulty
          </label>
          <select
            id="difficulty"
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-databricks-500"
          >
            <option value="">Any difficulty</option>
            {DIFFICULTIES.map((d) => (
              <option key={d} value={d}>
                {d.charAt(0).toUpperCase() + d.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3">
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={handleStart}
          disabled={loading}
          className="w-full bg-databricks-500 hover:bg-databricks-600 disabled:opacity-50 text-white font-medium py-2.5 rounded transition-colors"
        >
          {loading ? 'Loading…' : 'Start Session'}
        </button>
      </div>
    </div>
  )
}
