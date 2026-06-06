import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { SessionProvider, useSession } from './SessionContext'
import * as api from '../api'

vi.mock('../api')

const EXERCISES = [
  {
    exerciseId: 'q1',
    type: 'single_choice',
    domain: 'Data Governance',
    difficulty: 'easy',
    question: 'Q1?',
    codeContext: null,
    displayedOptions: [
      { id: 'a', text: 'A' },
      { id: 'b', text: 'B' },
      { id: 'c', text: 'C' },
      { id: 'd', text: 'D' },
    ],
  },
  {
    exerciseId: 'q2',
    type: 'single_choice',
    domain: 'Production Pipelines',
    difficulty: 'medium',
    question: 'Q2?',
    codeContext: null,
    displayedOptions: [
      { id: 'a', text: 'A' },
      { id: 'b', text: 'B' },
      { id: 'c', text: 'C' },
      { id: 'd', text: 'D' },
    ],
  },
]

function setup() {
  const wrapper = ({ children }) => <SessionProvider>{children}</SessionProvider>
  return renderHook(() => useSession(), { wrapper })
}

describe('SessionContext', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

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
    expect(result.current.currentExercise.exerciseId).toBe('q1')
  })

  it('grades via the backend and stores the full feedback response', async () => {
    api.submitFeedback.mockResolvedValue({
      correct: true,
      correctOptionId: 'a',
      explanation: 'because',
      references: ['https://example.com'],
    })
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.setSelection('q1', 'a'))
    await act(async () => {
      await result.current.submitAnswer('q1')
    })

    expect(api.submitFeedback).toHaveBeenCalledWith({
      exerciseId: 'q1',
      displayedOptionIds: ['a', 'b', 'c', 'd'],
      selectedId: 'a',
    })
    expect(result.current.feedback.q1).toEqual({
      correct: true,
      correctOptionId: 'a',
      explanation: 'because',
      references: ['https://example.com'],
    })
  })

  it('records incorrect feedback from the backend', async () => {
    api.submitFeedback.mockResolvedValue({
      correct: false,
      correctOptionId: 'b',
      explanation: 'nope',
      references: [],
    })
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.setSelection('q2', 'a'))
    await act(async () => {
      await result.current.submitAnswer('q2')
    })
    expect(result.current.feedback.q2.correct).toBe(false)
  })

  it('does not re-submit an already-answered question', async () => {
    api.submitFeedback.mockResolvedValue({
      correct: true,
      correctOptionId: 'a',
      explanation: 'x',
      references: [],
    })
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.setSelection('q1', 'a'))
    await act(async () => {
      await result.current.submitAnswer('q1')
    })
    await act(async () => {
      await result.current.submitAnswer('q1')
    })
    expect(api.submitFeedback).toHaveBeenCalledTimes(1)
  })

  it('does not submit when nothing is selected', async () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    await act(async () => {
      await result.current.submitAnswer('q1')
    })
    expect(api.submitFeedback).not.toHaveBeenCalled()
    expect(result.current.feedback.q1).toBeUndefined()
  })

  it('clears the submitting flag if grading fails', async () => {
    api.submitFeedback.mockRejectedValue(new Error('down'))
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.setSelection('q1', 'a'))
    await act(async () => {
      await result.current.submitAnswer('q1')
    })
    expect(result.current.feedback.q1).toBeUndefined()
    expect(result.current.submitting.q1).toBeUndefined()
  })

  it('advances to the next exercise and then to summary', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.next())
    expect(result.current.currentIndex).toBe(1)
    expect(result.current.currentExercise.exerciseId).toBe('q2')
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
    act(() => result.current.setSelection('q1', 'a'))
    const firstSelection = result.current.selectedAnswers
    act(() => result.current.setSelection('q2', 'b'))
    expect(result.current.selectedAnswers).not.toBe(firstSelection)
    expect(firstSelection.q2).toBeUndefined()
  })
})
