import { useState, useEffect } from 'react'
import { useSession } from '../context/SessionContext'
import { getStats, getReadiness } from '../api'
import ReadinessIndicator from '../components/ReadinessIndicator'
import { EXAMS, DEFAULT_EXAM } from '../constants'

/**
 * Stats dashboard (FR-23/FR-25). Shows overall accuracy + total attempts, a
 * per-Domain accuracy table with weak Domains visually distinct, a lightweight
 * trend viz, and a ReadinessIndicator. Handles loading / error / empty-history
 * (all zeros) gracefully.
 *
 * Weak Domains are highlighted using the readiness per-Domain `ready` flag when
 * available, otherwise by comparing accuracy to the readiness threshold (~0.7).
 */

function pct(n) {
  if (typeof n !== 'number' || Number.isNaN(n)) return '0%'
  return `${Math.round(n * 100)}%`
}

const EMPTY_OVERALL = { attempts: 0, correct: 0, accuracy: 0 }

export default function StatsDashboard() {
  const { reset } = useSession()
  const [exam, setExam] = useState(DEFAULT_EXAM)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(null)
  const [readiness, setReadiness] = useState(null)

  useEffect(() => {
    let ignore = false
    setLoading(true)
    setError(null)
    Promise.all([getStats({ exam }), getReadiness({ exam })])
      .then(([s, r]) => {
        if (ignore) return
        setStats(s)
        setReadiness(r)
      })
      .catch((e) => {
        if (ignore) return
        setError(e.message || 'Failed to load stats. Is the backend running?')
      })
      .finally(() => {
        if (!ignore) setLoading(false)
      })
    return () => {
      ignore = true
    }
  }, [exam])

  const overall = stats?.overall ?? EMPTY_OVERALL
  const byDomain = stats?.byDomain ?? {}
  const trend = Array.isArray(stats?.trend) ? stats.trend : []
  const domainEntries = Object.entries(byDomain)
  const hasHistory = (overall.attempts ?? 0) > 0

  // A Domain is "weak" when the accuracy shown for it is below the ~0.7 bar.
  // Highlight is based on the SAME (lifetime) accuracy figure displayed next to
  // it, so the red flag and the number never contradict. (Rolling-window
  // readiness is surfaced separately by the ReadinessIndicator below.)
  const threshold =
    typeof readiness?.threshold === 'number' ? readiness.threshold : 0.7
  function isWeak(accuracy) {
    return accuracy < threshold
  }

  const maxTrendAttempts = trend.reduce(
    (m, t) => Math.max(m, t.attempts || 0),
    0
  )

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between gap-4 mb-6">
        <h2 className="text-2xl font-semibold text-gray-900">Your stats</h2>
        <div className="flex items-center gap-2">
          <label htmlFor="stats-exam" className="text-sm font-medium text-gray-700">
            Exam
          </label>
          <select
            id="stats-exam"
            value={exam}
            onChange={(e) => setExam(e.target.value)}
            className="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-databricks-500"
          >
            <option value={EXAMS.ASSOCIATE}>Associate</option>
            <option value={EXAMS.PROFESSIONAL}>Professional</option>
          </select>
        </div>
      </div>

      {loading && (
        <p className="text-gray-600" data-testid="stats-loading">
          Loading your stats…
        </p>
      )}

      {error && (
        <div
          role="alert"
          className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3"
        >
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="space-y-6">
          {/* Overall summary. */}
          <section
            aria-labelledby="overall-heading"
            className="bg-white border border-gray-200 rounded-lg p-6"
          >
            <h3 id="overall-heading" className="text-lg font-semibold text-gray-900">
              Overall
            </h3>
            {!hasHistory ? (
              <p className="mt-2 text-gray-600" data-testid="stats-empty">
                No practice history yet. Finish a session and your accuracy and
                weak areas will show up here.
              </p>
            ) : (
              <div className="mt-3 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Accuracy</p>
                  <p
                    className="text-3xl font-bold text-databricks-600"
                    data-testid="overall-accuracy"
                  >
                    {pct(overall.accuracy)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Attempts</p>
                  <p
                    className="text-3xl font-bold text-gray-900"
                    data-testid="overall-attempts"
                  >
                    {overall.attempts}
                  </p>
                  <p className="text-xs text-gray-500">{overall.correct} correct</p>
                </div>
              </div>
            )}
          </section>

          {/* Readiness guidance. */}
          <ReadinessIndicator readiness={readiness} />

          {/* Per-domain accuracy with weak domains highlighted. */}
          {domainEntries.length > 0 && (
            <section
              aria-labelledby="by-domain-heading"
              className="bg-white border border-gray-200 rounded-lg p-6"
            >
              <h3
                id="by-domain-heading"
                className="text-lg font-semibold text-gray-900 mb-3"
              >
                By domain
              </h3>
              <ul className="space-y-3" data-testid="stats-by-domain">
                {domainEntries.map(([domain, d]) => {
                  const weak = isWeak(d.accuracy)
                  return (
                    <li
                      key={domain}
                      data-testid={`stats-domain-${domain}`}
                      data-weak={weak ? 'true' : 'false'}
                      className={`rounded p-2 ${weak ? 'bg-red-50 ring-1 ring-red-200' : ''}`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm text-gray-800">
                          {domain}
                          {weak && (
                            <span className="ml-2 text-xs font-semibold text-red-700">
                              Needs work
                            </span>
                          )}
                        </span>
                        <span className="text-sm text-gray-700">
                          <span
                            className={`font-semibold ${weak ? 'text-red-700' : 'text-green-700'}`}
                          >
                            {pct(d.accuracy)}
                          </span>{' '}
                          <span className="text-gray-500">
                            ({d.correct}/{d.attempts})
                          </span>
                        </span>
                      </div>
                      <div className="mt-1 h-2 w-full rounded bg-gray-200">
                        <div
                          className={`h-2 rounded ${weak ? 'bg-red-500' : 'bg-green-500'}`}
                          style={{ width: pct(d.accuracy) }}
                        />
                      </div>
                    </li>
                  )
                })}
              </ul>
            </section>
          )}

          {/* Lightweight trend viz. */}
          {trend.length > 0 && (
            <section
              aria-labelledby="trend-heading"
              className="bg-white border border-gray-200 rounded-lg p-6"
            >
              <h3
                id="trend-heading"
                className="text-lg font-semibold text-gray-900 mb-3"
              >
                Trend
              </h3>
              <ul className="space-y-2" data-testid="stats-trend">
                {trend.map((t) => (
                  <li
                    key={t.date}
                    className="flex items-center gap-3 text-sm"
                    data-testid={`trend-${t.date}`}
                  >
                    <span className="w-24 shrink-0 text-gray-600">{t.date}</span>
                    <span className="flex-1">
                      <span className="block h-3 rounded bg-gray-200">
                        <span
                          className="block h-3 rounded bg-databricks-500"
                          style={{
                            width:
                              maxTrendAttempts > 0
                                ? `${Math.round(((t.attempts || 0) / maxTrendAttempts) * 100)}%`
                                : '0%',
                          }}
                        />
                      </span>
                    </span>
                    <span className="w-28 shrink-0 text-right text-gray-700">
                      {pct(t.accuracy)} · {t.attempts}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <div>
            <button
              type="button"
              onClick={reset}
              className="bg-databricks-500 hover:bg-databricks-600 text-white font-medium py-2.5 px-5 rounded transition-colors"
            >
              Back to Start
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
