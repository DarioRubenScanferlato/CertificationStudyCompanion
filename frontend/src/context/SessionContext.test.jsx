import { describe, it, expect } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { SessionProvider, useSession } from './SessionContext'

const EXERCISES = [
  {
    id: 'q1',
    type: 'single_choice',
    domain: 'Data Governance',
    difficulty: 'easy',
    question: 'Q1?',
    explanation: 'because',
    references: [],
    options: [
      { id: 'a', text: 'A', correct: true },
      { id: 'b', text: 'B', correct: false },
    ],
    answer: ['a'],
  },
  {
    id: 'q2',
    type: 'multi_choice',
    domain: 'Production Pipelines',
    difficulty: 'medium',
    question: 'Q2?',
    explanation: 'reasons',
    references: [],
    options: [
      { id: 'a', text: 'A', correct: true },
      { id: 'b', text: 'B', correct: true },
      { id: 'c', text: 'C', correct: false },
    ],
    answer: ['a', 'b'],
  },
]

function setup() {
  const wrapper = ({ children }) => <SessionProvider>{children}</SessionProvider>
  return renderHook(() => useSession(), { wrapper })
}

describe('SessionContext', () => {
  it('starts on the select view', () => {
    const { result } = setup()
    expect(result.current.view).toBe('select')
    expect(result.current.total).toBe(0)
  })

  it('startSession populates exercises and switches to practice', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    expect(result.current.view).toBe('practice')
    expect(result.current.total).toBe(2)
    expect(result.current.currentExercise.id).toBe('q1')
  })

  it('records correct feedback on submit', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.setSelection('q1', ['a']))
    act(() => result.current.submitAnswer('q1'))
    expect(result.current.feedback.q1.correct).toBe(true)
  })

  it('records incorrect feedback for a wrong multi-select', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.setSelection('q2', ['a']))
    act(() => result.current.submitAnswer('q2'))
    expect(result.current.feedback.q2.correct).toBe(false)
  })

  it('advances to the next exercise and then to summary', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.next())
    expect(result.current.currentIndex).toBe(1)
    expect(result.current.currentExercise.id).toBe('q2')
    act(() => result.current.next())
    expect(result.current.view).toBe('summary')
  })

  it('reset returns to the initial select state', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.reset())
    expect(result.current.view).toBe('select')
    expect(result.current.total).toBe(0)
  })

  it('does not mutate selection state across updates (immutability)', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.setSelection('q1', ['a']))
    const firstSelection = result.current.selectedAnswers
    act(() => result.current.setSelection('q2', ['b']))
    expect(result.current.selectedAnswers).not.toBe(firstSelection)
    expect(firstSelection.q2).toBeUndefined()
  })
})
