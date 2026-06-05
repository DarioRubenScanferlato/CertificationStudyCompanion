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
 * - correct options -> green
 * - user-selected but wrong -> red
 * - everything else -> neutral
 */
function optionFeedbackClass(optionId, { isCorrectOption, isSelected }) {
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
    feedback,
    setSelection,
    submitAnswer,
    next,
  } = useSession()

  if (!currentExercise) return null

  const exercise = currentExercise
  const isMulti = exercise.type === EXERCISE_TYPES.MULTI_CHOICE
  const selected = selectedAnswers[exercise.id] || []
  const result = feedback[exercise.id]
  const submitted = Boolean(result)
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

  // Defensive guard: a malformed exercise with no options would otherwise throw
  // in the options.map below and white-screen the whole app (no error boundary).
  if (!Array.isArray(exercise.options) || exercise.options.length === 0) {
    return (
      <UnsupportedExercise
        message="This exercise is malformed (no answer options)."
        isLast={isLast}
        onNext={next}
      />
    )
  }

  function toggleOption(optionId) {
    if (submitted) return
    if (isMulti) {
      const nextSel = selected.includes(optionId)
        ? selected.filter((id) => id !== optionId)
        : [...selected, optionId]
      setSelection(exercise.id, nextSel)
    } else {
      setSelection(exercise.id, [optionId])
    }
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
        {isMulti && (
          <p className="mt-3 text-sm italic text-gray-500">Select all that apply.</p>
        )}
      </div>

      {/* Options */}
      <div className="space-y-3" role="group" aria-label="Answer options">
        {exercise.options.map((opt) => {
          const isSelected = selected.includes(opt.id)
          const isCorrectOption = submitted && opt.correct
          const stateClass = submitted
            ? optionFeedbackClass(opt.id, { isCorrectOption, isSelected })
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
                type={isMulti ? 'checkbox' : 'radio'}
                name={`answer-${exercise.id}`}
                value={opt.id}
                checked={isSelected}
                disabled={submitted}
                onChange={() => toggleOption(opt.id)}
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
        <button
          type="button"
          onClick={() => submitAnswer(exercise.id)}
          disabled={selected.length === 0}
          className="mt-6 w-full bg-databricks-500 hover:bg-databricks-600 disabled:opacity-50 text-white font-medium py-2.5 rounded transition-colors"
        >
          Submit
        </button>
      ) : (
        <Feedback exercise={exercise} result={result} isLast={isLast} onNext={next} />
      )}
    </div>
  )
}

function Feedback({ exercise, result, isLast, onNext }) {
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
        <p className="text-gray-800 whitespace-pre-wrap">{exercise.explanation}</p>

        {exercise.references && exercise.references.length > 0 && (
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-1">References</h3>
            <ul className="list-disc list-inside space-y-1">
              {exercise.references.map((ref, i) => (
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
