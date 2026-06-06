import { createContext, useContext, useMemo, useReducer, useRef } from 'react'
import { submitFeedback } from '../api'

/**
 * Session state shape:
 * - view: 'select' | 'practice' | 'summary'
 * - exercises: SessionEntry[]        (the active session's questions; each has
 *     { exerciseId, type, domain, difficulty, question, codeContext,
 *       displayedOptions: [{ id, text }] })
 * - currentIndex: number             (index into exercises)
 * - selectedAnswers: {exerciseId: string} (single selected option id per exercise)
 * - submitting: {exerciseId: true}   (in-flight grading requests)
 * - submitErrors: {exerciseId: string} (last grading error, if the submit failed)
 * - feedback: {exerciseId: {correct, correctOptionId, explanation, references}}
 *     (recorded after the backend grades each exercise)
 */
const initialState = {
  view: 'select',
  exercises: [],
  currentIndex: 0,
  selectedAnswers: {},
  submitting: {},
  submitErrors: {},
  feedback: {},
}

function sessionReducer(state, action) {
  switch (action.type) {
    case 'START_SESSION':
      return {
        ...initialState,
        exercises: action.exercises,
        view: 'practice',
      }

    case 'SET_SELECTION':
      return {
        ...state,
        selectedAnswers: {
          ...state.selectedAnswers,
          [action.exerciseId]: action.optionId,
        },
      }

    case 'SUBMIT_START': {
      // Starting a (re)submit clears any prior error for this exercise.
      const submitErrors = { ...state.submitErrors }
      delete submitErrors[action.exerciseId]
      return {
        ...state,
        submitting: { ...state.submitting, [action.exerciseId]: true },
        submitErrors,
      }
    }

    case 'SUBMIT_SUCCESS': {
      const submitting = { ...state.submitting }
      delete submitting[action.exerciseId]
      const submitErrors = { ...state.submitErrors }
      delete submitErrors[action.exerciseId]
      return {
        ...state,
        submitting,
        submitErrors,
        feedback: {
          ...state.feedback,
          [action.exerciseId]: action.result,
        },
      }
    }

    case 'SUBMIT_ERROR': {
      const submitting = { ...state.submitting }
      delete submitting[action.exerciseId]
      return {
        ...state,
        submitting,
        submitErrors: {
          ...state.submitErrors,
          [action.exerciseId]: action.error || 'Could not grade your answer.',
        },
      }
    }

    case 'NEXT': {
      const isLast = state.currentIndex >= state.exercises.length - 1
      if (isLast) {
        return { ...state, view: 'summary' }
      }
      return { ...state, currentIndex: state.currentIndex + 1 }
    }

    case 'RESET':
      return { ...initialState }

    default:
      return state
  }
}

const SessionContext = createContext(null)

export function SessionProvider({ children }) {
  const [state, dispatch] = useReducer(sessionReducer, initialState)

  // Mirror the parts of state the async submit needs, so submitAnswer can read
  // current values without being recreated (and without stale closures).
  const stateRef = useRef(state)
  stateRef.current = state

  const value = useMemo(() => {
    const currentExercise = state.exercises[state.currentIndex] || null

    async function submitAnswer(exerciseId) {
      const s = stateRef.current
      // Once submitted, an answer is final — ignore re-submits. Also ignore a
      // submit that's already in flight.
      if (s.feedback[exerciseId] || s.submitting[exerciseId]) return
      const exercise = s.exercises.find((e) => e.exerciseId === exerciseId)
      if (!exercise) return
      const selectedId = s.selectedAnswers[exerciseId]
      // Nothing selected -> nothing to grade.
      if (!selectedId) return

      const displayedOptionIds = (exercise.displayedOptions || []).map((o) => o.id)

      dispatch({ type: 'SUBMIT_START', exerciseId })
      try {
        const result = await submitFeedback({
          exerciseId,
          displayedOptionIds,
          selectedId,
        })
        dispatch({ type: 'SUBMIT_SUCCESS', exerciseId, result })
      } catch (err) {
        dispatch({
          type: 'SUBMIT_ERROR',
          exerciseId,
          error: err?.message || 'Could not grade your answer. Please try again.',
        })
      }
    }

    return {
      ...state,
      currentExercise,
      total: state.exercises.length,
      // actions
      startSession: (exercises) => dispatch({ type: 'START_SESSION', exercises }),
      setSelection: (exerciseId, optionId) =>
        dispatch({ type: 'SET_SELECTION', exerciseId, optionId }),
      submitAnswer,
      next: () => dispatch({ type: 'NEXT' }),
      reset: () => dispatch({ type: 'RESET' }),
    }
  }, [state])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

/**
 * Access session state and actions. Must be used within a SessionProvider.
 */
export function useSession() {
  const ctx = useContext(SessionContext)
  if (ctx === null) {
    throw new Error('useSession must be used within a SessionProvider')
  }
  return ctx
}
