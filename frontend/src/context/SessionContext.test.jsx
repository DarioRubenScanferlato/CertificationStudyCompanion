import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { SessionProvider, useSession } from './SessionContext'
import { computeResults } from '../pages/Summary'
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

  // --- Story 6.3: feedback retention, back, skip, end-to-summary ---

  it('initializes the new lifecycle fields', () => {
    const { result } = setup()
    expect(result.current.sessionState).toBe('active')
    expect(result.current.questionState).toEqual({})
    expect(result.current.furthestIndex).toBe(0)
  })

  it('marks a question answered and retains full feedback across navigation', async () => {
    const fullResult = {
      correct: true,
      correctOptionId: 'a',
      explanation: 'because',
      references: ['https://example.com'],
    }
    api.submitFeedback.mockResolvedValue(fullResult)
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.setSelection('q1', 'a'))
    await act(async () => {
      await result.current.submitAnswer('q1')
    })
    expect(result.current.questionState.q1).toBe('answered')
    expect(result.current.feedback.q1).toEqual(fullResult)

    // Navigate forward then back — feedback must survive unchanged.
    act(() => result.current.next())
    expect(result.current.currentIndex).toBe(1)
    act(() => result.current.prev())
    expect(result.current.currentIndex).toBe(0)
    expect(result.current.feedback.q1).toEqual(fullResult)
    expect(result.current.questionState.q1).toBe('answered')
  })

  it('prev shows an answered question read-only and never re-POSTs', async () => {
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
    const feedbackAfterSubmit = result.current.feedback.q1

    act(() => result.current.next())
    act(() => result.current.prev())
    // Re-submitting a revisited, already-answered question is a no-op.
    await act(async () => {
      await result.current.submitAnswer('q1')
    })
    expect(api.submitFeedback).toHaveBeenCalledTimes(1)
    expect(result.current.feedback.q1).toBe(feedbackAfterSubmit)
  })

  it('prev is a no-op on the first question', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.prev())
    expect(result.current.currentIndex).toBe(0)
  })

  it('skip advances, records unanswered (skipped), and calls no API', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.skip())
    expect(result.current.questionState.q1).toBe('skipped')
    expect(result.current.feedback.q1).toBeUndefined()
    expect(api.submitFeedback).not.toHaveBeenCalled()
    expect(result.current.currentIndex).toBe(1)
    expect(result.current.furthestIndex).toBe(1)
  })

  it('excludes skipped questions from the scored total', async () => {
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
    act(() => result.current.skip()) // skip q2
    const { correct, answered } = computeResults(
      result.current.exercises,
      result.current.feedback,
    )
    expect(answered).toBe(1)
    expect(correct).toBe(1)
  })

  it('endToSummary scores only the answered subset (partial summary)', async () => {
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
    act(() => result.current.skip()) // q2 skipped, now at last (no further)
    act(() => result.current.endToSummary())

    expect(result.current.sessionState).toBe('ended-early')
    expect(result.current.view).toBe('summary')
    const { correct, answered, total } = computeResults(
      result.current.exercises,
      result.current.feedback,
    )
    expect(answered).toBe(1)
    expect(correct).toBe(1)
    expect(total).toBe(2)
  })

  it('keeps furthestIndex monotonic across next/skip/prev', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    expect(result.current.furthestIndex).toBe(0)
    act(() => result.current.next()) // -> index 1, furthest 1
    expect(result.current.furthestIndex).toBe(1)
    act(() => result.current.prev()) // -> index 0, furthest stays 1
    expect(result.current.currentIndex).toBe(0)
    expect(result.current.furthestIndex).toBe(1)
    act(() => result.current.skip()) // skip q1 -> index 1, furthest stays 1
    expect(result.current.furthestIndex).toBe(1)
  })

  it('advancing past the last question completes the session', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.next())
    act(() => result.current.next()) // past last
    expect(result.current.view).toBe('summary')
    expect(result.current.sessionState).toBe('completed')
  })

  it('skipping the last question completes the session', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.next())
    act(() => result.current.skip()) // skip last -> summary/completed
    expect(result.current.view).toBe('summary')
    expect(result.current.sessionState).toBe('completed')
    expect(result.current.questionState.q2).toBe('skipped')
  })

  it('reset and startSession return the new fields to initial', () => {
    const { result } = setup()
    act(() => result.current.startSession(EXERCISES))
    act(() => result.current.skip())
    act(() => result.current.reset())
    expect(result.current.sessionState).toBe('active')
    expect(result.current.questionState).toEqual({})
    expect(result.current.furthestIndex).toBe(0)

    act(() => result.current.startSession(EXERCISES))
    expect(result.current.sessionState).toBe('active')
    expect(result.current.questionState).toEqual({})
    expect(result.current.furthestIndex).toBe(0)
  })
})
