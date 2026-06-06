import { useState, useEffect } from 'react'
import { useSession } from '../context/SessionContext'
import { getSession, getExerciseCount } from '../api'
import { DOMAINS_BY_EXAM, DIFFICULTIES, EXAMS, DEFAULT_EXAM } from '../constants'

/**
 * Landing page: pick filters and start a practice session.
 */
export default function SessionSelect() {
  const { startSession } = useSession()
  // Exam scopes the session so Associate + Professional never mix. It defaults
  // to Associate and is ALWAYS sent to the API (never omitted).
  const [exam, setExam] = useState(DEFAULT_EXAM)
  const [domain, setDomain] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [count, setCount] = useState(null)
  const [countLoading, setCountLoading] = useState(false)

  // The Domain dropdown is scoped to the selected exam's domains.
  const domainOptions = DOMAINS_BY_EXAM[exam] ?? []

  // When the exam changes, clear any selected domain so a stale Professional
  // domain can't persist into an Associate selection (and vice versa).
  function handleExamChange(nextExam) {
    setExam(nextExam)
    setDomain('')
  }

  // Live match count: refresh whenever the filters change so the user can
  // right-size a session before starting (UX-DR9). An ignore flag drops stale
  // responses when filters change faster than the requests resolve.
  useEffect(() => {
    let ignore = false
    setCountLoading(true)
    getExerciseCount({
      exam,
      domain: domain || undefined,
      difficulty: difficulty || undefined,
    })
      .then((n) => {
        if (!ignore) setCount(n)
      })
      .catch(() => {
        if (!ignore) setCount(null)
      })
      .finally(() => {
        if (!ignore) setCountLoading(false)
      })
    return () => {
      ignore = true
    }
  }, [exam, domain, difficulty])

  async function handleStart() {
    setLoading(true)
    setError(null)
    try {
      const sessionEntries = await getSession({
        exam,
        domain: domain || undefined,
        difficulty: difficulty || undefined,
      })
      if (!sessionEntries || sessionEntries.length === 0) {
        setError('No exercises match those filters. Try broadening your selection.')
        return
      }
      startSession(sessionEntries)
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
          <label htmlFor="exam" className="block text-sm font-medium text-gray-700 mb-1">
            Exam
          </label>
          <select
            id="exam"
            value={exam}
            onChange={(e) => handleExamChange(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-databricks-500"
          >
            <option value={EXAMS.ASSOCIATE}>Associate</option>
            <option value={EXAMS.PROFESSIONAL}>Professional</option>
          </select>
        </div>

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
            {domainOptions.map((d) => (
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

        {count !== null && !countLoading && (
          <p
            className={`text-sm ${count === 0 ? 'text-amber-700' : 'text-gray-600'}`}
            data-testid="match-count"
          >
            {count === 0
              ? 'No questions match these filters'
              : `${count} ${count === 1 ? 'question matches' : 'questions match'}`}
          </p>
        )}

        {error && (
          <div role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3">
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={handleStart}
          disabled={loading || count === 0}
          className="w-full bg-databricks-500 hover:bg-databricks-600 disabled:opacity-50 text-white font-medium py-2.5 rounded transition-colors"
        >
          {loading ? 'Loading…' : 'Start Session'}
        </button>
      </div>
    </div>
  )
}
