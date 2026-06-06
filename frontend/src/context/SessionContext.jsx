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
 *     (recorded after the backend grades each exercise; retained for read-only
 *      revisit and review — answers are final, never re-graded)
 * - sessionState: 'active' | 'ended-early' | 'completed'
 *     ('active' during practice; 'completed' when advanced past the last
 *      question; 'ended-early' when the user ends to Summary early)
 * - questionState: {exerciseId: 'unanswered' | 'answered' | 'skipped'}
 *     (absent key is treated as 'unanswered')
 * - furthestIndex: number            (furthest-reached question index; never
 *      decremented, so Back/Next can't overrun the visited range)
 */
const initialState = {
  view: 'select',
  exercises: [],
  currentIndex: 0,
  selectedAnswers: {},
  submitting: {},
  submitErrors: {},
  feedback: {},
  sessionState: 'active',
  questionState: {},
  furthestIndex: 0,
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
        questionState: {
          ...state.questionState,
          [action.exerciseId]: 'answered',
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
        return { ...state, view: 'summary', sessionState: 'completed' }
      }
      const nextIndex = state.currentIndex + 1
      return {
        ...state,
        currentIndex: nextIndex,
        furthestIndex: Math.max(state.furthestIndex, nextIndex),
      }
    }

    case 'PREV': {
      // Read-only back: move to an earlier question. No-op at index 0. Does not
      // touch feedback/selections/submitting/furthestIndex — answers stay final.
      if (state.currentIndex <= 0) return state
      return { ...state, currentIndex: state.currentIndex - 1 }
    }

    case 'SKIP': {
      // Skip records the current question as unanswered (not incorrect) and
      // advances like NEXT. Only meaningful before submit; if the question is
      // already answered, leave its state untouched and just advance.
      const alreadyAnswered = Boolean(state.feedback[action.exerciseId])
      const questionState = alreadyAnswered
        ? state.questionState
        : { ...state.questionState, [action.exerciseId]: 'skipped' }

      const isLast = state.currentIndex >= state.exercises.length - 1
      if (isLast) {
        return {
          ...state,
          questionState,
          view: 'summary',
          sessionState: 'completed',
        }
      }
      const nextIndex = state.currentIndex + 1
      return {
        ...state,
        questionState,
        currentIndex: nextIndex,
        furthestIndex: Math.max(state.furthestIndex, nextIndex),
      }
    }

    case 'GO_STATS':
      // Navigate to the read-only Stats dashboard. Clears any active session so
      // returning to Start lands on a fresh select screen.
      return { ...initialState, view: 'stats' }

    case 'END_TO_SUMMARY':
      // End the session early -> Summary over the answered subset. Feedback and
      // questionState are preserved so computeResults scores what was answered.
      return { ...state, view: 'summary', sessionState: 'ended-early' }

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
      prev: () => dispatch({ type: 'PREV' }),
      skip: () => dispatch({ type: 'SKIP', exerciseId: currentExercise?.exerciseId }),
      endToSummary: () => dispatch({ type: 'END_TO_SUMMARY' }),
      goStats: () => dispatch({ type: 'GO_STATS' }),
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
