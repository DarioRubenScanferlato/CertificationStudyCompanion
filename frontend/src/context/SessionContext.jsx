import { createContext, useContext, useMemo, useReducer } from 'react'
import { gradeAnswer } from '../utils/grading'

/**
 * Session state shape:
 * - view: 'select' | 'practice' | 'summary'
 * - exercises: Exercise[]            (the active session's questions)
 * - currentIndex: number             (index into exercises)
 * - selectedAnswers: {id: string[]}  (current selection per exercise)
 * - feedback: {id: {correct, answer}} (recorded after submitting each exercise)
 */
const initialState = {
  view: 'select',
  exercises: [],
  currentIndex: 0,
  selectedAnswers: {},
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
          [action.exerciseId]: action.optionIds,
        },
      }

    case 'SUBMIT_ANSWER': {
      const exercise = state.exercises.find((e) => e.id === action.exerciseId)
      if (!exercise) return state
      // Once submitted, an answer is final — ignore re-submits.
      if (state.feedback[action.exerciseId]) return state
      const selected = state.selectedAnswers[action.exerciseId] || []
      // Nothing selected -> nothing to grade.
      if (selected.length === 0) return state
      const correct = gradeAnswer(selected, exercise.answer)
      return {
        ...state,
        feedback: {
          ...state.feedback,
          [action.exerciseId]: { correct, answer: exercise.answer },
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

  const value = useMemo(() => {
    const currentExercise = state.exercises[state.currentIndex] || null
    return {
      ...state,
      currentExercise,
      total: state.exercises.length,
      // actions
      startSession: (exercises) => dispatch({ type: 'START_SESSION', exercises }),
      setSelection: (exerciseId, optionIds) =>
        dispatch({ type: 'SET_SELECTION', exerciseId, optionIds }),
      submitAnswer: (exerciseId) => dispatch({ type: 'SUBMIT_ANSWER', exerciseId }),
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
