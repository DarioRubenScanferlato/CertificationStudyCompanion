import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Summary, { computeResults } from './Summary'
import * as api from '../api'
import { useSession } from '../context/SessionContext'

vi.mock('../api')
vi.mock('../context/SessionContext')

const EXERCISES = [
  { exerciseId: 'q1', domain: 'Data Governance' },
  { exerciseId: 'q2', domain: 'Data Governance' },
  { exerciseId: 'q3', domain: 'Production Pipelines' },
]

describe('computeResults', () => {
  it('totals correct answers across the session', () => {
    const feedback = {
      q1: { correct: true },
      q2: { correct: false },
      q3: { correct: true },
    }
    const r = computeResults(EXERCISES, feedback)
    expect(r.correct).toBe(2)
    expect(r.answered).toBe(3)
    expect(r.total).toBe(3)
  })

  it('breaks results down per domain', () => {
    const feedback = {
      q1: { correct: true },
      q2: { correct: false },
      q3: { correct: true },
    }
    const r = computeResults(EXERCISES, feedback)
    expect(r.byDomain['Data Governance']).toEqual({ correct: 1, total: 2 })
    expect(r.byDomain['Production Pipelines']).toEqual({ correct: 1, total: 1 })
  })

  it('only counts answered exercises', () => {
    const feedback = { q1: { correct: true } }
    const r = computeResults(EXERCISES, feedback)
    expect(r.answered).toBe(1)
    expect(r.correct).toBe(1)
    expect(r.byDomain['Production Pipelines']).toBeUndefined()
  })

  it('surfaces skipped and unanswered counts from questionState', () => {
    const feedback = { q1: { correct: true } }
    const questionState = { q2: 'skipped' }
    const r = computeResults(EXERCISES, feedback, questionState)
    expect(r.answered).toBe(1)
    expect(r.skipped).toBe(1)
    // q3 has no feedback and no questionState entry -> unanswered, not incorrect.
    expect(r.unanswered).toBe(1)
  })
})

// Session entries carry displayedOptions for the review-incorrect resolver.
const REVIEW_EXERCISES = [
  {
    exerciseId: 'q1',
    domain: 'Data Governance',
    question: 'What is Unity Catalog?',
    displayedOptions: [
      { id: 'a', text: 'A governance solution' },
      { id: 'b', text: 'A storage format' },
    ],
  },
  {
    exerciseId: 'q2',
    domain: 'Data Governance',
    question: 'What does Auto Loader do?',
    displayedOptions: [
      { id: 'a', text: 'Incrementally ingests files' },
      { id: 'b', text: 'Deletes data' },
    ],
  },
  {
    exerciseId: 'q3',
    domain: 'Production Pipelines',
    question: 'Pick the right pipeline mode',
    displayedOptions: [
      { id: 'a', text: 'Triggered' },
      { id: 'b', text: 'Continuous' },
    ],
  },
]

const startSession = vi.fn()
const reset = vi.fn()

function mockSession(overrides = {}) {
  useSession.mockReturnValue({
    exercises: REVIEW_EXERCISES,
    feedback: {},
    questionState: {},
    sessionState: 'completed',
    startSession,
    reset,
    ...overrides,
  })
}

describe('Summary component', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  describe('review-incorrect list', () => {
    it('renders only missed questions with their correct option and explanation', () => {
      mockSession({
        feedback: {
          q1: { correct: true, correctOptionId: 'a', explanation: 'right' },
          q2: {
            correct: false,
            correctOptionId: 'a',
            explanation: 'Auto Loader ingests files incrementally.',
          },
          q3: { correct: true, correctOptionId: 'b', explanation: 'ok' },
        },
      })
      render(<Summary />)

      // Only the missed question appears in the review list.
      expect(screen.getByText('Review incorrect (1)')).toBeInTheDocument()
      expect(screen.getByText('What does Auto Loader do?')).toBeInTheDocument()
      // The two correctly-answered questions are not listed for review.
      expect(screen.queryByText('What is Unity Catalog?')).not.toBeInTheDocument()
      expect(screen.queryByText('Pick the right pipeline mode')).not.toBeInTheDocument()

      // Expand to reveal the resolved correct option + explanation.
      fireEvent.click(screen.getByText('What does Auto Loader do?'))
      expect(screen.getByText('Incrementally ingests files')).toBeInTheDocument()
      expect(
        screen.getByText('Auto Loader ingests files incrementally.')
      ).toBeInTheDocument()
    })

    it('omits the review list when nothing was missed', () => {
      mockSession({
        feedback: {
          q1: { correct: true, correctOptionId: 'a' },
          q2: { correct: true, correctOptionId: 'a' },
          q3: { correct: true, correctOptionId: 'b' },
        },
      })
      render(<Summary />)
      expect(screen.queryByText(/Review incorrect/)).not.toBeInTheDocument()
    })
  })

  describe('practice these N again', () => {
    it('replays exactly the missed ids and starts a session', async () => {
      const replaySession = [{ exerciseId: 'q2' }]
      api.getSessionByIds.mockResolvedValue(replaySession)
      mockSession({
        feedback: {
          q1: { correct: true, correctOptionId: 'a' },
          q2: { correct: false, correctOptionId: 'a' },
          q3: { correct: true, correctOptionId: 'b' },
        },
      })
      render(<Summary />)

      const btn = screen.getByRole('button', { name: 'Practice these 1 again' })
      fireEvent.click(btn)

      await waitFor(() =>
        expect(api.getSessionByIds).toHaveBeenCalledWith(['q2'])
      )
      expect(startSession).toHaveBeenCalledWith(replaySession)
    })

    it('does NOT start a session and shows an error when the replay comes back empty', async () => {
      // Guards the blank-Practice-screen dead-end: an empty replay result must
      // not push an empty session into the runner.
      api.getSessionByIds.mockResolvedValue([])
      mockSession({
        feedback: {
          q1: { correct: true, correctOptionId: 'a' },
          q2: { correct: false, correctOptionId: 'a' },
          q3: { correct: true, correctOptionId: 'b' },
        },
      })
      render(<Summary />)

      fireEvent.click(screen.getByRole('button', { name: 'Practice these 1 again' }))

      await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument())
      expect(startSession).not.toHaveBeenCalled()
      // The replay buttons re-enable (replaying flag was reset).
      expect(screen.getByRole('button', { name: 'Practice these 1 again' })).not.toBeDisabled()
    })

    it('shows the live missed count in the label', () => {
      mockSession({
        feedback: {
          q1: { correct: false, correctOptionId: 'a' },
          q2: { correct: false, correctOptionId: 'a' },
        },
      })
      render(<Summary />)
      expect(
        screen.getByRole('button', { name: 'Practice these 2 again' })
      ).toBeInTheDocument()
    })

    it('is hidden when nothing was missed', () => {
      mockSession({
        feedback: {
          q1: { correct: true, correctOptionId: 'a' },
          q2: { correct: true, correctOptionId: 'a' },
          q3: { correct: true, correctOptionId: 'b' },
        },
      })
      render(<Summary />)
      expect(screen.queryByRole('button', { name: /Practice these/ })).not.toBeInTheDocument()
    })
  })

  describe('restart this session', () => {
    it('replays the full id set and starts a session', async () => {
      const replaySession = [{ exerciseId: 'q1' }, { exerciseId: 'q2' }, { exerciseId: 'q3' }]
      api.getSessionByIds.mockResolvedValue(replaySession)
      mockSession({
        feedback: {
          q1: { correct: true, correctOptionId: 'a' },
          q2: { correct: false, correctOptionId: 'a' },
          q3: { correct: true, correctOptionId: 'b' },
        },
      })
      render(<Summary />)

      fireEvent.click(screen.getByRole('button', { name: 'Restart this session' }))

      await waitFor(() =>
        expect(api.getSessionByIds).toHaveBeenCalledWith(['q1', 'q2', 'q3'])
      )
      expect(startSession).toHaveBeenCalledWith(replaySession)
    })
  })

  describe('partial / ended-early counts', () => {
    it('scores over the answered subset and surfaces skipped + unanswered', () => {
      mockSession({
        sessionState: 'ended-early',
        feedback: {
          q1: { correct: true, correctOptionId: 'a' },
        },
        questionState: { q2: 'skipped' },
      })
      render(<Summary />)

      // Denominator is the answered subset (1), not the total (3). The headline
      // score node renders "1/1" (split across text nodes), so match the
      // databricks-500 score element by class to disambiguate from per-domain.
      const headline = document.querySelector('.text-databricks-500')
      expect(headline).toHaveTextContent('1/1')
      expect(screen.getByText('100% correct')).toBeInTheDocument()
      // Surfaced partial counts: 1 answered, 1 skipped, 1 unanswered of 3.
      expect(
        screen.getByText(/1 answered · 1 skipped · 1 unanswered of 3/)
      ).toBeInTheDocument()
    })

    it('shows the encouraging 0-answered state when all skipped', () => {
      mockSession({
        sessionState: 'ended-early',
        feedback: {},
        questionState: { q1: 'skipped', q2: 'skipped', q3: 'skipped' },
      })
      render(<Summary />)

      expect(
        screen.getByText('Nothing graded yet — jump back in?')
      ).toBeInTheDocument()
      // No score headline, no per-domain block, no practice-again action.
      expect(screen.queryByText(/correct$/)).not.toBeInTheDocument()
      expect(screen.queryByText('By domain')).not.toBeInTheDocument()
      expect(screen.queryByRole('button', { name: /Practice these/ })).not.toBeInTheDocument()
      // Restart + Start a new session are still offered.
      expect(
        screen.getByRole('button', { name: 'Restart this session' })
      ).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: 'Start a new session' })
      ).toBeInTheDocument()
    })
  })

  it('Start a new session calls reset', () => {
    mockSession({
      feedback: { q1: { correct: true, correctOptionId: 'a' } },
    })
    render(<Summary />)
    fireEvent.click(screen.getByRole('button', { name: 'Start a new session' }))
    expect(reset).toHaveBeenCalled()
  })
})
