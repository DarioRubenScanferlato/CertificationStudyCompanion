import { useSession } from '../context/SessionContext'
import { EXERCISE_TYPES } from '../constants'
import QuestionContent from '../components/QuestionContent'

const DIFFICULTY_STYLES = {
  easy: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  hard: 'bg-red-100 text-red-800',
}

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

export default function MCQPractice() {
  const {
    currentExercise,
    currentIndex,
    total,
    selectedAnswers,
    submitting,
    submitErrors,
    feedback,
    setSelection,
    submitAnswer,
    next,
  } = useSession()

  if (!currentExercise) return null

  const exercise = currentExercise
  const selected = selectedAnswers[exercise.exerciseId]
  const result = feedback[exercise.exerciseId]
  const submitted = Boolean(result)
  const isSubmitting = Boolean(submitting[exercise.exerciseId])
  const submitError = submitErrors[exercise.exerciseId]
  const isLast = currentIndex >= total - 1

  // Code-completion exercises get their own UI in a later epic. Until then,
  // degrade gracefully rather than rendering them as a broken MCQ.
  if (exercise.type === EXERCISE_TYPES.CODE_COMPLETION) {
    return (
      <UnsupportedExercise
        message="Code-completion exercises arrive in a later update."
        isLast={isLast}
        onNext={next}
      />
    )
  }

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
      {/* Progress + metadata */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-medium text-gray-500">
          Question {currentIndex + 1} of {total}
        </span>
        <div className="flex gap-2">
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
        </div>
      </div>

      {/* Question */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-5">
        <QuestionContent text={exercise.question} />
      </div>

      {/* Options */}
      <div className="space-y-3" role="radiogroup" aria-label="Answer options">
        {exercise.displayedOptions.map((opt) => {
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
                className="mt-1"
              />
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
            onClick={() => submitAnswer(exercise.exerciseId)}
            disabled={!selected || isSubmitting}
            className="mt-4 w-full bg-databricks-500 hover:bg-databricks-600 disabled:opacity-50 text-white font-medium py-2.5 rounded transition-colors"
          >
            {isSubmitting ? 'Submitting…' : submitError ? 'Retry' : 'Submit'}
          </button>
        </>
      ) : (
        <Feedback result={result} isLast={isLast} onNext={next} />
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

      <div className="mt-4 bg-white border border-gray-200 rounded-lg p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-1">Explanation</h3>
        <p className="text-gray-800 whitespace-pre-wrap">{result.explanation}</p>

        {result.references && result.references.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-1">References</h3>
            <ul className="list-disc list-inside space-y-1">
              {result.references.map((ref, i) => (
                <li key={`${ref}-${i}`}>
                  <a
                    href={ref}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-databricks-500 hover:underline break-all"
                  >
                    {ref}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={onNext}
        className="mt-5 w-full bg-gray-900 hover:bg-gray-700 text-white font-medium py-2.5 rounded transition-colors"
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
