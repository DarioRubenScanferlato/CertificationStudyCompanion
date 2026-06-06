import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import App from './App'
import * as api from './api'

vi.mock('./api')

describe('App Component', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    // SessionSelect fetches a live match count on mount; give it a resolved
    // promise so the Start screen renders without unhandled rejections.
    api.getExerciseCount.mockResolvedValue(0)
  })

  it('renders the app header', () => {
    render(<App />)
    expect(
      screen.getByText(/Databricks DE Certification Study Companion/i)
    ).toBeInTheDocument()
  })

  it('shows the SessionSelect page by default', () => {
    render(<App />)
    expect(screen.getByText(/Start a practice session/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Start Session/i })).toBeInTheDocument()
  })

  it('exposes the header title as a clickable Home affordance', () => {
    render(<App />)
    const home = screen.getByRole('button', { name: /go home/i })
    expect(home).toBeInTheDocument()
    // On Start it routes home (reset) — stays on the Start screen, no crash.
    fireEvent.click(home)
    expect(screen.getByRole('button', { name: /Start Session/i })).toBeInTheDocument()
  })

  it('navigates to the Stats view via the header Stats affordance and back', async () => {
    api.getStats.mockResolvedValue({
      overall: { attempts: 5, correct: 4, accuracy: 0.8 },
      byDomain: {},
      trend: [],
    })
    api.getReadiness.mockResolvedValue({
      overall: { accuracy: 0.8, ready: true, window: 50 },
      byDomain: {},
      threshold: 0.7,
      window: 50,
    })

    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: 'Stats' }))

    expect(await screen.findByText(/Your stats/i)).toBeInTheDocument()
    expect(await screen.findByTestId('overall-accuracy')).toHaveTextContent('80%')
    // The Stats affordance is hidden while on the Stats view.
    expect(screen.queryByRole('button', { name: 'Stats' })).not.toBeInTheDocument()

    // Return to Start.
    fireEvent.click(screen.getByRole('button', { name: /Back to Start/i }))
    expect(await screen.findByRole('button', { name: /Start Session/i })).toBeInTheDocument()
  })

  it('hides the Stats affordance during an active Practice session', async () => {
    api.getExerciseCount.mockResolvedValue(1)
    api.getSession.mockResolvedValue([
      {
        exerciseId: 'q1',
        type: 'single_choice',
        domain: 'Data Governance',
        difficulty: 'easy',
        question: 'What is Unity Catalog?',
        codeContext: null,
        displayedOptions: [
          { id: 'a', text: 'A governance solution' },
          { id: 'b', text: 'B' },
          { id: 'c', text: 'C' },
          { id: 'd', text: 'D' },
        ],
      },
    ])

    render(<App />)
    fireEvent.click(screen.getByRole('button', { name: /Start Session/i }))
    await screen.findByText(/Question 1 of 1/)
    expect(screen.queryByRole('button', { name: 'Stats' })).not.toBeInTheDocument()
  })

  it('on Practice, clicking the header Home routes through the Exit confirm', async () => {
    // Drive a real session into Practice, answer one question, then click Home.
    api.getExerciseCount.mockResolvedValue(1)
    api.getSession.mockResolvedValue([
      {
        exerciseId: 'q1',
        type: 'single_choice',
        domain: 'Data Governance',
        difficulty: 'easy',
        question: 'What is Unity Catalog?',
        codeContext: null,
        displayedOptions: [
          { id: 'a', text: 'A governance solution' },
          { id: 'b', text: 'B' },
          { id: 'c', text: 'C' },
          { id: 'd', text: 'D' },
        ],
      },
    ])
    api.submitFeedback.mockResolvedValue({
      correct: true,
      correctOptionId: 'a',
      explanation: 'x',
      references: [],
    })

    render(<App />)
    // Start the session.
    fireEvent.click(screen.getByRole('button', { name: /Start Session/i }))
    await screen.findByText(/Question 1 of 1/)

    // Answer so there's progress to protect.
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    await screen.findByText(/Correct!/)

    // Click the header Home -> Exit confirm appears (same flow as End session).
    fireEvent.click(screen.getByRole('button', { name: /go home/i }))
    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(within(dialog).getByText(/You've answered 1 of 1\./)).toBeInTheDocument()
  })
})
