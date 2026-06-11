import { useCallback, useEffect, useRef, useState } from 'react'
import { useSession } from '../context/SessionContext'
import { EXERCISE_TYPES } from '../constants'
import { DIFFICULTY_STYLES, FOCUS_RING, FOCUS_RING_NEUTRAL } from '../styles/ui'
import { useSessionExit } from '../hooks/useSessionExit'
import QuestionContent from '../components/QuestionContent'
import ConfirmDialog from '../components/ConfirmDialog'
import ProgressBar from '../components/ProgressBar'
import ExplanationPanel from '../components/ExplanationPanel'
import FeedbackNote from '../components/FeedbackNote'
import Timer from '../components/Timer'
import SeenIndicator from '../components/SeenIndicator'

/**
 * Compute the CSS classes for an option row once feedback is shown:
 * - the correct option -> green
 * - user-selected but wrong -> red
 * - everything else -> neutral
 */
function optionFeedbackClass({ isCorrectOption, isSelected }) {
  if (isCorrectOption) return 'border-green-500 bg-green-50'
  if (isSelected) return 'border-red-500 bg-red-50'
  return 'border-gray-200'
}

// True when the keydown originated from a text field — we don't want our
// single-key accelerators to hijack typing.
function isFromTextInput(target) {
  if (!target) return false
  const tag = target.tagName
  if (tag === 'INPUT') {
    const type = (target.getAttribute('type') || 'text').toLowerCase()
    // Radio/checkbox inputs are not "typing" targets; everything else is.
    return type !== 'radio' && type !== 'checkbox'
  }
  return tag === 'TEXTAREA' || target.isContentEditable === true
}

export default function MCQPractice() {
  const {
    currentExercise,
    currentIndex,
    total,
    exercises,
    selectedAnswers,
    submitting,
    submitErrors,
    feedback,
    setSelection,
    submitAnswer,
    next,
    prev,
    skip,
    endToSummary,
    timerDurationSeconds,
  } = useSession()

  const [hintsOpen, setHintsOpen] = useState(false)
  const endButtonRef = useRef(null)

  // Per-question timing (Story 8.2 / FR-28). The clock starts when a question
  // is presented and re-arms on every question change, so timing is strictly
  // per-question, never a cumulative session stopwatch. performance.now() is
  // monotonic so clock adjustments can't yield a negative duration.
  const questionStartRef = useRef(null)
  const currentExerciseId = currentExercise?.exerciseId
  useEffect(() => {
    questionStartRef.current = performance.now()
  }, [currentExerciseId])

  // Submit the current answer with its measured elapsed time. Both the Submit
  // button and the Enter shortcut route through here so timing is always sent.
  const submitWithTiming = useCallback(
    (exerciseId) => {
      const start = questionStartRef.current
      const elapsedMs =
        start == null ? undefined : Math.max(0, Math.round(performance.now() - start))
      submitAnswer(exerciseId, elapsedMs)
    },
    [submitAnswer]
  )

  // Number of answered questions (those with retained feedback) — drives the
  // Exit-confirm copy and the zero-answered shortcut.
  const answeredCount = exercises.filter((e) => Boolean(feedback[e.exerciseId])).length
  // Running correct count for the progress bar.
  const correctCount = exercises.filter((e) => feedback[e.exerciseId]?.correct).length

  // Exit-confirm wiring (shared with the Code-Completion runner via the hook).
  // Skip the prompt and exit straight to Start when nothing is answered.
  const { confirmOpen, requestExit, closeConfirm, handleSeeResults, handleDiscard } =
    useSessionExit({ skipConfirm: answeredCount === 0 })

  // --- Keyboard shortcuts --------------------------------------------------
  // A single document-level keydown handler, scoped to this view (removed on
  // unmount). It reads live state through a ref so the closure never goes
  // stale, and every action it triggers also has a clickable equivalent.
  const handlerRef = useRef(null)
  handlerRef.current = (event) => {
    // Defer to the modal's own Esc / focus trap while it's open, and never
    // hijack typing in text fields.
    if (confirmOpen) return
    if (event.defaultPrevented) return
    if (event.altKey || event.ctrlKey || event.metaKey) return
    if (isFromTextInput(event.target)) return

    const ex = currentExercise
    if (!ex) return
    const options = Array.isArray(ex.displayedOptions) ? ex.displayedOptions : []
    const isMcq =
      ex.type !== EXERCISE_TYPES.CODE_COMPLETION && options.length === 4
    const sel = selectedAnswers[ex.exerciseId]
    const fb = feedback[ex.exerciseId]
    const isSubmitted = Boolean(fb)
    const inFlight = Boolean(submitting[ex.exerciseId])

    const key = event.key
    const targetTag = event.target?.tagName
    const onRadio =
      targetTag === 'INPUT' &&
      (event.target.getAttribute('type') || '').toLowerCase() === 'radio'

    if (key === 'Escape') {
      event.preventDefault()
      requestExit()
      return
    }

    // Don't hijack ArrowLeft/Right when an answer radio has focus — native
    // radiogroup navigation must select options (ARIA contract). Back/Skip
    // arrows still work from anywhere else (e.g. focus on body or a button).
    if (key === 'ArrowLeft') {
      if (onRadio) return
      event.preventDefault()
      prev()
      return
    }

    if (key === 'ArrowRight') {
      if (onRadio) return
      event.preventDefault()
      if (isSubmitted) next()
      else skip()
      return
    }

    if (key === 'Enter') {
      // If a button has focus, let its native activation handle Enter so we
      // don't fire the action twice (global handler + button click).
      if (targetTag === 'BUTTON') return
      event.preventDefault()
      if (isSubmitted) {
        next()
      } else if (isMcq && sel && !inFlight) {
        submitWithTiming(ex.exerciseId)
      }
      return
    }

    // Option selection: 1-4 or a-d. No-op once submitted / mid-flight, and only
    // for a well-formed MCQ.
    if (!isMcq || isSubmitted || inFlight) return
    let idx = -1
    if (key >= '1' && key <= '4') idx = Number(key) - 1
    else {
      const lower = key.toLowerCase()
      if (lower >= 'a' && lower <= 'd') idx = lower.charCodeAt(0) - 97
    }
    if (idx >= 0 && idx < options.length) {
      event.preventDefault()
      setSelection(ex.exerciseId, options[idx].id)
    }
  }

  useEffect(() => {
    const onKeyDown = (event) => handlerRef.current?.(event)
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [])

  if (!currentExercise) return null

  const exercise = currentExercise
  const selected = selectedAnswers[exercise.exerciseId]
  const result = feedback[exercise.exerciseId]
  const submitted = Boolean(result)
  const isSubmitting = Boolean(submitting[exercise.exerciseId])
  const submitError = submitErrors[exercise.exerciseId]
  const isLast = currentIndex >= total - 1
  const isFirst = currentIndex === 0

  // Live announcement for the result + progress, read by aria-live below.
  const progressPhrase = `Progress: ${currentIndex + 1} of ${total}, ${correctCount} correct.`
  const announcement = submitted
    ? `Answer ${result.correct ? 'correct' : 'incorrect'}. ${progressPhrase}`
    : progressPhrase

  // Code-completion exercises are routed to CodeCompletion.jsx by the App
  // PracticeRouter (Epic 4 / Story 4.1), so they never reach MCQPractice. The
  // malformed-options guard below remains the defensive fallback.

  // Defensive guard: a malformed exercise without exactly 4 displayed options
  // would otherwise render as a broken question. Degrade instead of crashing.
  if (
    !Array.isArray(exercise.displayedOptions) ||
    exercise.displayedOptions.length !== 4
  ) {
    return (
      <UnsupportedExercise
        message="This exercise is malformed (expected 4 answer options)."
        isLast={isLast}
        onNext={next}
      />
    )
  }

  function selectOption(optionId) {
    if (submitted || isSubmitting) return
    setSelection(exercise.exerciseId, optionId)
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* aria-live announcer for correctness result + progress changes. */}
      <p aria-live="polite" className="sr-only">
        {announcement}
      </p>

      {/* Progress + metadata */}
      <div className="flex items-center gap-4 mb-4">
        <ProgressBar
          current={currentIndex + 1}
          total={total}
          correct={correctCount}
        />
        <div className="flex items-center gap-2 shrink-0">
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
          {/* Seen-before indicator (Story 7.6): a quiet grey eye when this
              exercise has a recorded attempt. Renders nothing otherwise. */}
          <SeenIndicator seen={exercise.seen} />
          {/* Optional session countdown (Story 8.1). Renders only when the
              session was started timed; at zero it auto-ends to the partial
              Summary via endToSummary. Untimed sessions render nothing here. */}
          {timerDurationSeconds ? (
            <Timer durationSeconds={timerDurationSeconds} onExpire={endToSummary} />
          ) : null}
          {/* Persistent, neutral End-session control — visually subordinate to
              the databricks-500 Submit button so it never competes with it. */}
          <button
            ref={endButtonRef}
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
        description={`You've answered ${answeredCount} of ${total}.`}
        onDismiss={closeConfirm}
        actions={[
          { label: 'See results', onClick: handleSeeResults, variant: 'primary' },
          { label: 'Discard & exit', onClick: handleDiscard, variant: 'danger' },
          { label: 'Keep practicing', onClick: closeConfirm, variant: 'neutral' },
        ]}
      />

      {/* Navigation + keyboard hints */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={prev}
            disabled={isFirst}
            aria-label="Back to previous question"
            className={`text-sm px-3 py-1.5 rounded border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors ${FOCUS_RING}`}
          >
            ← Back
          </button>
          {!submitted && (
            <button
              type="button"
              onClick={skip}
              aria-label="Skip this question"
              className={`text-sm px-3 py-1.5 rounded border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition-colors ${FOCUS_RING}`}
            >
              Skip →
            </button>
          )}
        </div>
        <KeyboardHints open={hintsOpen} onToggle={() => setHintsOpen((o) => !o)} />
      </div>

      {/* Question */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-5">
        <QuestionContent text={exercise.question} />
      </div>

      {/* Options */}
      <div className="space-y-3" role="radiogroup" aria-label="Answer options">
        {exercise.displayedOptions.map((opt, i) => {
          const isSelected = selected === opt.id
          const isCorrectOption = submitted && opt.id === result.correctOptionId
          const stateClass = submitted
            ? optionFeedbackClass({ isCorrectOption, isSelected })
            : isSelected
              ? 'border-databricks-500 bg-databricks-50'
              : 'border-gray-200 hover:border-gray-300'

          return (
            <label
              key={opt.id}
              className={`flex items-start gap-3 border rounded-lg p-4 cursor-pointer transition-colors ${stateClass} ${
                submitted ? 'cursor-default' : ''
              }`}
            >
              <input
                type="radio"
                name={`answer-${exercise.exerciseId}`}
                value={opt.id}
                checked={isSelected}
                disabled={submitted || isSubmitting}
                onChange={() => selectOption(opt.id)}
                className={`mt-1 ${FOCUS_RING}`}
              />
              <span aria-hidden="true" className="font-medium text-gray-400">
                {i + 1}.
              </span>
              <span className="text-gray-900">{opt.text}</span>
              {isCorrectOption && (
                <span aria-hidden="true" className="ml-auto text-green-700 font-medium">
                  ✓
                </span>
              )}
            </label>
          )
        })}
      </div>

      {/* Submit / Feedback */}
      {!submitted ? (
        <>
          {submitError && (
            <div
              role="alert"
              className="mt-6 text-sm text-red-700 bg-red-50 border border-red-200 rounded p-3"
            >
              {submitError} Please try again.
            </div>
          )}
          <button
            type="button"
            onClick={() => submitWithTiming(exercise.exerciseId)}
            disabled={!selected || isSubmitting}
            className={`mt-4 w-full bg-databricks-500 hover:bg-databricks-600 disabled:opacity-50 text-white font-medium py-2.5 rounded transition-colors ${FOCUS_RING}`}
          >
            {isSubmitting ? 'Submitting…' : submitError ? 'Retry' : 'Submit'}
          </button>
        </>
      ) : (
        <>
          <Feedback result={result} isLast={isLast} onNext={next} />
          {/* key on exerciseId remounts the note control per question, so a typed
              draft or "saved" confirmation never carries onto another question. */}
          <FeedbackNote key={exercise.exerciseId} exerciseId={exercise.exerciseId} />
        </>
      )}
    </div>
  )
}

/**
 * Discoverable keyboard-shortcut affordance. A toggle button reveals the map;
 * the map itself is just text so it never traps focus.
 */
function KeyboardHints({ open, onToggle }) {
  return (
    <div className="relative">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        aria-label="Keyboard shortcuts"
        className={`text-xs px-2 py-1 rounded border border-gray-300 bg-white text-gray-600 hover:bg-gray-50 transition-colors ${FOCUS_RING}`}
      >
        ⌨ Shortcuts
      </button>
      {open && (
        <div className="absolute right-0 z-10 mt-1 w-64 rounded-lg border border-gray-200 bg-white p-3 text-xs text-gray-700 shadow-lg">
          <ul className="space-y-1">
            <li>
              <kbd className="font-mono">1–4</kbd> / <kbd className="font-mono">a–d</kbd>{' '}
              — select an option
            </li>
            <li>
              <kbd className="font-mono">Enter</kbd> — submit, then advance
            </li>
            <li>
              <kbd className="font-mono">←</kbd> — back (read-only)
            </li>
            <li>
              <kbd className="font-mono">→</kbd> — next / skip
            </li>
            <li>
              <kbd className="font-mono">Esc</kbd> — end session
            </li>
          </ul>
        </div>
      )}
    </div>
  )
}

function Feedback({ result, isLast, onNext }) {
  return (
    <div className="mt-6">
      <div
        role="status"
        className={`rounded-lg p-4 font-semibold ${
          result.correct ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}
      >
        {result.correct ? 'Correct!' : 'Incorrect'}{' '}
        <span aria-hidden="true">{result.correct ? '✓' : '✗'}</span>
      </div>

      <ExplanationPanel explanation={result.explanation} references={result.references} />

      <button
        type="button"
        onClick={onNext}
        className={`mt-5 w-full bg-gray-900 hover:bg-gray-700 text-white font-medium py-2.5 rounded transition-colors ${FOCUS_RING}`}
      >
        {isLast ? 'See Results' : 'Next'}
      </button>
    </div>
  )
}

/**
 * Shown for exercises this page can't render (unsupported type or malformed
 * data). Lets the user move on instead of hitting a dead end / blank screen.
 */
function UnsupportedExercise({ message, isLast, onNext }) {
  return (
    <div className="max-w-3xl mx-auto">
      <div
        role="status"
        className="rounded-lg p-4 bg-yellow-50 border border-yellow-200 text-yellow-800"
      >
        {message}
      </div>
      <button
        type="button"
        onClick={onNext}
        className="mt-5 w-full bg-gray-900 hover:bg-gray-700 text-white font-medium py-2.5 rounded transition-colors"
      >
        {isLast ? 'See Results' : 'Skip'}
      </button>
    </div>
  )
}
