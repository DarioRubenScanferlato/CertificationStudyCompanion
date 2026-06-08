import { useState } from 'react'
import { useSession } from '../context/SessionContext'
import { getSessionByIds } from '../api'
import { PASS_THRESHOLD } from '../constants'

/**
 * Build overall and per-domain score breakdowns from the session feedback.
 * Only answered exercises count toward totals.
 *
 * Returns:
 *   correct     - number of answered exercises graded correct
 *   answered    - number of exercises with retained feedback (graded)
 *   total       - total exercises in the session
 *   byDomain    - { [domain]: { correct, total } } over answered exercises
 *   skipped     - exercises explicitly marked 'skipped' (questionState)
 *   unanswered  - exercises neither answered nor skipped (early-exit leftovers)
 *
 * The score denominator shown to the user is the answered subset; skipped and
 * unanswered counts are surfaced separately for partial / ended-early summaries
 * (EXPERIENCE.md ended-early). `skipped`/`unanswered` are read from the Story
 * 6.3 questionState, never inferred from "incorrect".
 */
export function computeResults(exercises, feedback, questionState = {}) {
  let correct = 0
  let answered = 0
  let skipped = 0
  let unanswered = 0
  const byDomain = {}

  for (const ex of exercises) {
    const result = feedback[ex.exerciseId]
    if (result) {
      answered += 1
      const bucket = byDomain[ex.domain] || { correct: 0, total: 0 }
      bucket.total += 1
      if (result.correct) {
        correct += 1
        bucket.correct += 1
      }
      byDomain[ex.domain] = bucket
      continue
    }
    // Not graded: classify by the Story 6.3 per-question state.
    if (questionState[ex.exerciseId] === 'skipped') {
      skipped += 1
    } else {
      unanswered += 1
    }
  }

  return { correct, answered, total: exercises.length, byDomain, skipped, unanswered }
}

export default function Summary() {
  const { exercises, feedback, questionState, startSession, reset, mode } = useSession()
  const { correct, answered, total, byDomain, skipped, unanswered } = computeResults(
    exercises,
    feedback,
    questionState
  )
  // Score is over the answered subset (ended-early summaries exclude skipped /
  // unanswered from the denominator shown).
  const pct = answered > 0 ? Math.round((correct / answered) * 100) : 0

  // Mock Exam (Story 8.4 / FR-27): an exam-style result. Unlike practice, a mock
  // scores over the FULL set (unanswered/skipped count against you, as on the
  // real exam) and is compared to the ~70% pass-bar heuristic — guidance, not a
  // guarantee. Practice summaries are unchanged.
  const isMock = mode === 'mock'
  const examPct = total > 0 ? Math.round((correct / total) * 100) : 0
  const passThresholdPct = Math.round(PASS_THRESHOLD * 100)
  const onTrack = total > 0 && examPct >= passThresholdPct

  // Exercises answered incorrectly, resolved against retained feedback only.
  const missed = exercises.filter((ex) => feedback[ex.exerciseId]?.correct === false)
  const missedIds = missed.map((ex) => ex.exerciseId)
  const allIds = exercises.map((ex) => ex.exerciseId)

  const [replaying, setReplaying] = useState(false)
  const [replayError, setReplayError] = useState(null)

  // Replay a set of exercise ids through POST /api/sessions, then begin a fresh
  // session with the (re-sampled, re-shuffled) result.
  async function replay(ids) {
    if (replaying) return
    setReplaying(true)
    setReplayError(null)
    try {
      const session = await getSessionByIds(ids)
      // Guard against an empty result (e.g. all ids now unknown after a content
      // change): starting an empty session would render a blank Practice page
      // with no way out. Stay on Summary and surface the problem instead.
      if (!Array.isArray(session) || session.length === 0) {
        setReplayError('These questions are no longer available. Try a new session.')
        setReplaying(false)
        return
      }
      startSession(session) // navigates away; Summary unmounts, so leave replaying set
    } catch (err) {
      setReplayError(err?.message || 'Could not start the session. Please try again.')
      setReplaying(false)
    }
  }

  const nothingGraded = answered === 0

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-2xl font-semibold text-gray-900 mb-6">
        {isMock ? 'Mock exam results' : 'Session complete'}
      </h2>

      {/* Exam-style readiness banner (mock only): overall vs the ~70% bar. */}
      {isMock && (
        <div
          data-testid="mock-result-banner"
          className={`rounded-lg p-5 mb-6 border ${
            onTrack
              ? 'bg-green-50 border-green-200'
              : 'bg-red-50 border-red-200'
          }`}
        >
          <div className="flex items-center justify-between gap-4">
            <div>
              <p
                className={`text-sm font-semibold ${
                  onTrack ? 'text-green-800' : 'text-red-800'
                }`}
              >
                {onTrack ? 'On track' : 'Below the pass bar'}{' '}
                <span aria-hidden="true">{onTrack ? '✓' : '✗'}</span>
              </p>
              <p className="text-xs text-gray-600 mt-1">
                {examPct}% correct ({correct}/{total}) vs a ~{passThresholdPct}% target — study
                guidance, not a guarantee of passing the exam.
              </p>
            </div>
            <span
              className={`text-4xl font-bold shrink-0 ${
                onTrack ? 'text-green-700' : 'text-red-700'
              }`}
            >
              {examPct}%
            </span>
          </div>
          {/* Track with a threshold marker, mirroring the ReadinessIndicator. */}
          <div className="relative mt-3 h-3 w-full rounded bg-gray-200">
            <div
              className={`h-3 rounded ${onTrack ? 'bg-green-500' : 'bg-red-500'}`}
              style={{ width: `${examPct}%` }}
            />
            <div
              className="absolute top-0 h-3 w-0.5 bg-gray-700"
              style={{ left: `${passThresholdPct}%` }}
              aria-hidden="true"
              data-testid="mock-threshold-marker"
            />
          </div>
        </div>
      )}

      {nothingGraded ? (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6 text-center">
          <p className="text-lg font-medium text-gray-900">Nothing graded yet — jump back in?</p>
          {skipped > 0 && (
            <p className="text-gray-600 mt-2">
              {skipped} skipped
              {unanswered > 0 ? ` · ${unanswered} unanswered` : ''}
            </p>
          )}
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6 text-center">
          <p className="text-5xl font-bold text-databricks-500">
            {correct}/{answered}
          </p>
          <p className="text-gray-600 mt-2">{pct}% correct</p>
          {(skipped > 0 || unanswered > 0) && (
            <p className="text-gray-500 text-sm mt-3">
              {answered} answered
              {skipped > 0 ? ` · ${skipped} skipped` : ''}
              {unanswered > 0 ? ` · ${unanswered} unanswered` : ''}
              {` of ${total}`}
            </p>
          )}
        </div>
      )}

      {!nothingGraded && (
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
      )}

      {missed.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Review incorrect ({missed.length})
          </h3>
          <ul className="space-y-3">
            {missed.map((ex) => (
              <ReviewItem
                key={ex.exerciseId}
                exercise={ex}
                feedback={feedback[ex.exerciseId]}
              />
            ))}
          </ul>
        </div>
      )}

      {replayError && (
        <div
          role="alert"
          className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-3 mb-4 text-sm"
        >
          {replayError}
        </div>
      )}

      <div className="space-y-3">
        {missedIds.length > 0 && (
          <button
            type="button"
            onClick={() => replay(missedIds)}
            disabled={replaying}
            className="w-full bg-databricks-500 hover:bg-databricks-600 disabled:opacity-60 text-white font-medium py-2.5 rounded transition-colors"
          >
            Practice these {missedIds.length} again
          </button>
        )}

        {allIds.length > 0 && (
          <button
            type="button"
            onClick={() => replay(allIds)}
            disabled={replaying}
            className="w-full bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-60 text-gray-800 font-medium py-2.5 rounded transition-colors"
          >
            Restart this session
          </button>
        )}

        <button
          type="button"
          onClick={reset}
          disabled={replaying}
          className="w-full bg-white border border-gray-300 hover:bg-gray-50 disabled:opacity-50 text-gray-800 font-medium py-2.5 rounded transition-colors"
        >
          Start a new session
        </button>
      </div>
    </div>
  )
}

/**
 * Expandable review entry for one missed question. Read-only over the retained
 * feedback: the correct option text is resolved from the exercise's
 * displayedOptions, and the explanation comes straight from feedback. No API
 * call, no re-grade.
 */
function ReviewItem({ exercise, feedback }) {
  const [open, setOpen] = useState(false)
  const correctOption = (exercise.displayedOptions || []).find(
    (o) => o.id === feedback?.correctOptionId
  )

  return (
    <li className="border border-gray-200 rounded">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="w-full text-left px-3 py-2 flex justify-between items-start gap-2 hover:bg-gray-50"
      >
        <span className="text-gray-900 text-sm">{exercise.question}</span>
        <span className="text-gray-400 text-sm shrink-0">{open ? '−' : '+'}</span>
      </button>
      {open && (
        <div className="px-3 pb-3 pt-1 border-t border-gray-200">
          <p className="text-sm">
            <span className="font-medium text-green-700">Correct answer: </span>
            <span className="text-gray-800">{correctOption?.text}</span>
          </p>
          {feedback?.explanation && (
            <p className="text-sm text-gray-600 mt-2">{feedback.explanation}</p>
          )}
        </div>
      )}
    </li>
  )
}
