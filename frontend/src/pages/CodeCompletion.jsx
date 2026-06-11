import { useEffect, useRef, useState } from 'react'
import { useSession } from '../context/SessionContext'
import { DIFFICULTY_STYLES, FOCUS_RING, FOCUS_RING_NEUTRAL } from '../styles/ui'
import { useSessionExit } from '../hooks/useSessionExit'
import CodeBlock from '../components/CodeBlock'
import ProgressBar from '../components/ProgressBar'
import ConfirmDialog from '../components/ConfirmDialog'
import ExplanationPanel from '../components/ExplanationPanel'
import FeedbackNote from '../components/FeedbackNote'
import FeedbackTokens, { AttemptsCounter, AnswerReveal } from '../components/FeedbackTokens'
import SeenIndicator from '../components/SeenIndicator'
import { computeFeedback } from '../utils/codeFeedback'
import { CODE_COMPLETION_MAX_ATTEMPTS } from '../constants'

/**
 * Code-Completion ("Wordle-style") runner page (Epic 4).
 *
 * Each guess is scored CLIENT-SIDE **per character** (`computeFeedback`, < 100ms,
 * NFR-1 — no server round-trip, no tokenizer; Story 4.8), rendered as per-letter
 * green/yellow/grey rows (`FeedbackTokens`), with a bounded attempt budget
 * (FR-15). On solve OR exhaustion the exercise concludes: the canonical answer is
 * revealed, the explanation/references show (FR-17), and Next advances via the
 * shared session machinery. A Skip control advances without revealing (FR-15).
 *
 * The concluded result is retained in SessionContext (`codeCompletionResults`)
 * so revisiting the exercise (Back/Next) shows it final — answers stay final,
 * matching the MCQ runner. Code-completion outcomes are client-side only — never
 * POSTed to /api/feedback and never recorded in the MCQ-scoped SQLite store, so
 * they don't feed stats/readiness/timing (known gap by design).
 */
export default function CodeCompletion() {
  const {
    currentExercise,
    currentIndex,
    total,
    exercises,
    feedback,
    next,
    codeCompletionResults,
    recordCodeCompletion,
  } = useSession()

  const [attempt, setAttempt] = useState('')
  const [history, setHistory] = useState([]) // tokenRows[] — one row per guess
  const [attemptsLeft, setAttemptsLeft] = useState(CODE_COMPLETION_MAX_ATTEMPTS)
  // Single source of truth for conclusion (replaces separate solved+concluded
  // booleans, which could encode an impossible "solved but not concluded" state).
  const [outcome, setOutcome] = useState(null) // null | 'solved' | 'exhausted'

  const exerciseId = currentExercise?.exerciseId

  // Read the retained results without making the restore effect depend on them
  // (it must re-run only on exercise change, not when we record the current one).
  const resultsRef = useRef(codeCompletionResults)
  resultsRef.current = codeCompletionResults

  // On exercise change: restore a previously-concluded result (so Back/Next shows
  // it final) or start fresh.
  useEffect(() => {
    const saved = resultsRef.current[exerciseId]
    if (saved) {
      setHistory(saved.history)
      setAttemptsLeft(saved.attemptsLeft)
      setOutcome(saved.outcome)
    } else {
      setHistory([])
      setAttemptsLeft(CODE_COMPLETION_MAX_ATTEMPTS)
      setOutcome(null)
    }
    setAttempt('')
  }, [exerciseId])

  // Exit-confirm wiring shared with the MCQ runner (Story 6.4).
  const { confirmOpen, requestExit, closeConfirm, handleSeeResults, handleDiscard } =
    useSessionExit()

  if (!currentExercise) return null

  const exercise = currentExercise
  const concluded = outcome !== null
  const solved = outcome === 'solved'
  const canSubmit = attempt.trim().length > 0 && !concluded
  const isLast = currentIndex >= total - 1
  // Running correct count comes from the shared session feedback (MCQ answers),
  // so the progress bar stays consistent across a mixed session instead of
  // resetting to 0 on every code-completion card.
  const correctCount = exercises.filter((e) => feedback[e.exerciseId]?.correct).length

  function handleGuess() {
    if (!canSubmit) return
    const fb = computeFeedback(attempt, exercise.answer, exercise.language, {
      accepted: exercise.accepted,
      caseSensitive: exercise.caseSensitive,
      ignoreWhitespace: exercise.ignoreWhitespace,
    })
    const newHistory = [...history, fb.tokens]
    const nextLeft = attemptsLeft - 1
    const newOutcome = fb.solved ? 'solved' : nextLeft <= 0 ? 'exhausted' : null

    setHistory(newHistory)
    setAttemptsLeft(nextLeft)
    setAttempt('')
    if (newOutcome) {
      setOutcome(newOutcome)
      // Retain so a revisit shows the final result rather than re-arming.
      recordCodeCompletion(exercise.exerciseId, {
        history: newHistory,
        attemptsLeft: nextLeft,
        outcome: newOutcome,
      })
    }
  }

  function handleInputKeyDown(e) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleGuess()
    }
  }

  // Skip (Story 4.8): advance to the next exercise WITHOUT revealing the answer
  // or explanation, so the learner is never forced to exhaust attempts. Distinct
  // from solve/exhaustion (which conclude + reveal); not recorded, so revisiting
  // a skipped exercise starts fresh.
  function handleSkip() {
    next()
  }

  const references = exercise.references || []

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress + metadata header (mirrors MCQPractice via the shared tokens). */}
      <div className="flex items-center gap-4 mb-4">
        <ProgressBar current={currentIndex + 1} total={total} correct={correctCount} />
        <div className="flex items-center gap-2 shrink-0">
          <AttemptsCounter attemptsLeft={attemptsLeft} max={CODE_COMPLETION_MAX_ATTEMPTS} />
          <span className="text-xs px-2 py-1 rounded bg-databricks-50 text-databricks-900">
            {exercise.domain}
          </span>
          <span
            className={`text-xs px-2 py-1 rounded capitalize ${
              DIFFICULTY_STYLES[exercise.difficulty] || 'bg-gray-100 text-gray-700'
            }`}
          >
            {exercise.difficulty}
          </span>
          {/* Seen-before indicator (Story 7.6). Code-Completion `seen` is
              always false today, but the wiring mirrors MCQPractice so it
              lights up automatically if CC attempts are ever recorded. */}
          <SeenIndicator seen={exercise.seen} />
          <button
            type="button"
            onClick={requestExit}
            className={`text-xs px-2 py-1 rounded border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition-colors ${FOCUS_RING_NEUTRAL}`}
          >
            End session
          </button>
        </div>
      </div>

      <ConfirmDialog
        open={confirmOpen}
        title="End this session?"
        description="Your progress so far will be summarized."
        onDismiss={closeConfirm}
        actions={[
          { label: 'See results', onClick: handleSeeResults, variant: 'primary' },
          { label: 'Discard & exit', onClick: handleDiscard, variant: 'danger' },
          { label: 'Keep practicing', onClick: closeConfirm, variant: 'neutral' },
        ]}
      />

      {/* Prompt */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4">
        <div className="flex items-center justify-between gap-3 mb-3">
          <h2 className="text-lg font-semibold text-gray-900">{exercise.prompt}</h2>
          <span
            className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700 font-mono uppercase shrink-0"
            data-testid="cc-language"
          >
            {exercise.language}
          </span>
        </div>

        {/* Template with the blank. CodeBlock preserves whitespace + highlights. */}
        <CodeBlock code={exercise.template} language={exercise.language} />
        <p className="mt-2 text-xs text-gray-500">
          Fill in the <code className="font-mono">___</code> blank.
        </p>
      </div>

      {/* Answer input + guess loop */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <label htmlFor="cc-attempt" className="block text-sm font-medium text-gray-700 mb-1">
          Your answer
        </label>
        <input
          id="cc-attempt"
          type="text"
          value={attempt}
          onChange={(e) => setAttempt(e.target.value)}
          onKeyDown={handleInputKeyDown}
          disabled={concluded}
          autoComplete="off"
          spellCheck={false}
          placeholder="Type the code that fills the blank…"
          className={`w-full border border-gray-300 rounded px-3 py-2 font-mono disabled:bg-gray-50 disabled:text-gray-500 ${FOCUS_RING}`}
        />

        {/* Attempt history — newest at the bottom; latest row carries the legend.
            Each tile is one character (per-letter Wordle feedback, Story 4.8). */}
        <div className="mt-3 min-h-[1.25rem]" data-testid="cc-attempts-region">
          {history.map((row, i) => (
            <FeedbackTokens key={i} tokens={row} showLegend={i === history.length - 1} />
          ))}
        </div>

        {!concluded && (
          <div className="mt-2 flex gap-2">
            <button
              type="button"
              onClick={handleGuess}
              disabled={!canSubmit}
              className={`flex-1 bg-databricks-500 hover:bg-databricks-600 disabled:opacity-50 text-white font-medium py-2.5 rounded transition-colors ${FOCUS_RING}`}
            >
              Submit guess
            </button>
            {/* Skip: advance without revealing — never forces exhausting attempts. */}
            <button
              type="button"
              onClick={handleSkip}
              className={`px-4 py-2.5 rounded border border-gray-300 bg-white text-gray-700 font-medium hover:bg-gray-50 transition-colors ${FOCUS_RING_NEUTRAL}`}
            >
              Skip
            </button>
          </div>
        )}

        {/* Conclusion: status, reveal, explanation/references, Next. */}
        {concluded && (
          <div className="mt-4">
            <div
              role="status"
              className={`rounded-lg p-4 font-semibold ${
                solved ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-900'
              }`}
            >
              {solved ? (
                <>
                  Solved in {history.length} {history.length === 1 ? 'try' : 'tries'}!{' '}
                  <span aria-hidden="true">✓</span>
                </>
              ) : (
                'Out of attempts — answer revealed'
              )}
            </div>

            <AnswerReveal revealed answer={exercise.answer} language={exercise.language} />

            <ExplanationPanel explanation={exercise.explanation} references={references} />

            <FeedbackNote key={exercise.exerciseId} exerciseId={exercise.exerciseId} />

            <button
              type="button"
              onClick={next}
              className={`mt-5 w-full bg-gray-900 hover:bg-gray-700 text-white font-medium py-2.5 rounded transition-colors ${FOCUS_RING}`}
            >
              {isLast ? 'See Results' : 'Next'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
