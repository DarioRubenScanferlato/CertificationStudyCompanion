import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { SessionProvider, useSession } from '../context/SessionContext'
import SessionSelect from './SessionSelect'
import * as api from '../api'

vi.mock('../api')

function renderPage() {
  return render(
    <SessionProvider>
      <SessionSelect />
    </SessionProvider>
  )
}

// A tiny probe that surfaces the real context state, so timer tests can assert
// what startSession threaded into the session without mocking the context.
function StateProbe() {
  const { view, timerDurationSeconds, mode } = useSession()
  return (
    <div>
      <span data-testid="view">{view}</span>
      <span data-testid="timer-seconds">{String(timerDurationSeconds)}</span>
      <span data-testid="mode">{mode}</span>
    </div>
  )
}

// Alias for the mock-flow tests (reads the same context state).
const MockProbe = StateProbe

function renderPageWithProbe() {
  return render(
    <SessionProvider>
      <SessionSelect />
      <StateProbe />
    </SessionProvider>
  )
}

describe('SessionSelect', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    // Default: a non-zero count so the live-count effect never rejects and
    // Start stays enabled unless a test overrides it.
    api.getExerciseCount.mockResolvedValue(10)
  })

  it('lists the Associate domains and difficulties by default', () => {
    renderPage()
    expect(screen.getByRole('option', { name: 'Databricks Intelligence Platform' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Governance and Security' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Easy' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Hard' })).toBeInTheDocument()
  })

  it('fetches exercises with the chosen filters (incl. exam) on Start', async () => {
    api.getSession.mockResolvedValue([{ id: 'q1' }])
    renderPage()

    fireEvent.change(screen.getByLabelText('Domain'), {
      target: { value: 'Governance and Security' },
    })
    fireEvent.change(screen.getByLabelText('Difficulty'), {
      target: { value: 'easy' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Start Session/i }))

    await waitFor(() =>
      expect(api.getSession).toHaveBeenCalledWith({
        exam: 'associate',
        domain: 'Governance and Security',
        difficulty: 'easy',
      })
    )
  })

  it('shows an error when no exercises match', async () => {
    api.getSession.mockResolvedValue([])
    renderPage()
    fireEvent.click(screen.getByRole('button', { name: /Start Session/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/no exercises match/i)
  })

  it('shows an error when the request fails', async () => {
    api.getSession.mockRejectedValue(new Error('Network error: down'))
    renderPage()
    fireEvent.click(screen.getByRole('button', { name: /Start Session/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/network error/i)
  })
})

describe('SessionSelect live match count', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    api.getSession.mockResolvedValue([{ id: 'q1' }])
  })

  it('renders the match count after mount', async () => {
    api.getExerciseCount.mockResolvedValue(42)
    renderPage()
    expect(await screen.findByTestId('match-count')).toHaveTextContent('42 questions match')
    expect(api.getExerciseCount).toHaveBeenCalledWith({
      exam: 'associate',
      domain: undefined,
      difficulty: undefined,
    })
  })

  it('refreshes the count when domain/difficulty change', async () => {
    api.getExerciseCount.mockResolvedValueOnce(42).mockResolvedValue(7)
    renderPage()
    await screen.findByText('42 questions match')

    fireEvent.change(screen.getByLabelText('Domain'), {
      target: { value: 'Governance and Security' },
    })

    expect(await screen.findByText('7 questions match')).toBeInTheDocument()
    await waitFor(() =>
      expect(api.getExerciseCount).toHaveBeenCalledWith({
        exam: 'associate',
        domain: 'Governance and Security',
        difficulty: undefined,
      })
    )
  })

  it('uses the singular form when exactly one question matches', async () => {
    api.getExerciseCount.mockResolvedValue(1)
    renderPage()
    expect(await screen.findByTestId('match-count')).toHaveTextContent('1 question matches')
  })

  it('disables Start and shows an empty-state message when count is 0', async () => {
    api.getExerciseCount.mockResolvedValue(0)
    renderPage()
    expect(await screen.findByText('No questions match these filters')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Start Session/i })).toBeDisabled()
  })

  it('keeps Start enabled when the count is non-zero', async () => {
    api.getExerciseCount.mockResolvedValue(5)
    renderPage()
    await screen.findByText('5 questions match')
    expect(screen.getByRole('button', { name: /Start Session/i })).not.toBeDisabled()
  })
})

describe('SessionSelect optional countdown (Story 8.1)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    api.getExerciseCount.mockResolvedValue(10)
    api.getSession.mockResolvedValue([{ exerciseId: 'q1' }])
  })

  it('hides the duration input until the timer is enabled', () => {
    renderPage()
    expect(screen.queryByLabelText('Duration (minutes)')).not.toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Timed session'))
    expect(screen.getByLabelText('Duration (minutes)')).toBeInTheDocument()
  })

  it('threads the chosen duration (seconds) into the started session', async () => {
    renderPageWithProbe()
    fireEvent.click(screen.getByLabelText('Timed session'))
    fireEvent.change(screen.getByLabelText('Duration (minutes)'), {
      target: { value: '15' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Start Session/i }))

    await waitFor(() => expect(screen.getByTestId('view')).toHaveTextContent('practice'))
    // 15 minutes -> 900 seconds.
    expect(screen.getByTestId('timer-seconds')).toHaveTextContent('900')
  })

  it('starts untimed (no duration) when the timer is off — parity', async () => {
    renderPageWithProbe()
    fireEvent.click(screen.getByRole('button', { name: /Start Session/i }))

    await waitFor(() => expect(screen.getByTestId('view')).toHaveTextContent('practice'))
    expect(screen.getByTestId('timer-seconds')).toHaveTextContent('null')
  })
})

describe('SessionSelect Mock Exam affordance (Story 8.4)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    api.getExerciseCount.mockResolvedValue(10)
  })

  it('renders a Mock Exam control with the selected exam’s duration copy', () => {
    renderPage()
    // Associate by default -> 90 min copy.
    expect(screen.getByRole('button', { name: /Mock Exam/i })).toHaveTextContent('90 min')
    fireEvent.change(screen.getByLabelText('Exam'), { target: { value: 'professional' } })
    expect(screen.getByRole('button', { name: /Mock Exam/i })).toHaveTextContent('120 min')
  })

  it('starts a mock run: calls getMockSession({exam}) and seeds mode + countdown', async () => {
    api.getMockSession.mockResolvedValue({
      entries: [{ exerciseId: 'm1' }],
      durationMinutes: 90,
    })
    render(
      <SessionProvider>
        <SessionSelect />
        <MockProbe />
      </SessionProvider>
    )
    fireEvent.click(screen.getByRole('button', { name: /Mock Exam/i }))

    await waitFor(() => expect(screen.getByTestId('view')).toHaveTextContent('practice'))
    expect(api.getMockSession).toHaveBeenCalledWith({ exam: 'associate' })
    expect(screen.getByTestId('mode')).toHaveTextContent('mock')
    // 90 minutes -> 5400 seconds seeds the countdown.
    expect(screen.getByTestId('timer-seconds')).toHaveTextContent('5400')
  })

  it('surfaces an error when no mock exam is available', async () => {
    api.getMockSession.mockResolvedValue({ entries: [], durationMinutes: null })
    renderPage()
    fireEvent.click(screen.getByRole('button', { name: /Mock Exam/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/no mock exam/i)
  })
})

describe('SessionSelect exam scoping (Story 6.7)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    api.getExerciseCount.mockResolvedValue(10)
    api.getSession.mockResolvedValue([{ id: 'q1' }])
  })

  function domainOptionNames() {
    const select = screen.getByLabelText('Domain')
    return Array.from(select.querySelectorAll('option'))
      .map((o) => o.textContent)
      .filter((t) => t !== 'All domains')
  }

  it('defaults the Exam selector to Associate', () => {
    renderPage()
    expect(screen.getByLabelText('Exam')).toHaveValue('associate')
  })

  it('lists exactly the 7 Associate sections (May 2026 blueprint) by default', () => {
    renderPage()
    const names = domainOptionNames()
    expect(names).toEqual([
      'Databricks Intelligence Platform',
      'Data Ingestion and Loading',
      'Data Transformation and Modeling',
      'Working with Lakeflow Jobs',
      'Implementing CI/CD',
      'Troubleshooting, Monitoring, and Optimization',
      'Governance and Security',
    ])
    expect(names).toHaveLength(7)
  })

  it('lists exactly the 10 Professional domains (incl. Data Governance) when Professional is selected', () => {
    renderPage()
    fireEvent.change(screen.getByLabelText('Exam'), {
      target: { value: 'professional' },
    })
    const names = domainOptionNames()
    expect(names).toHaveLength(10)
    expect(names).toContain('Developing Code for Data Processing')
    expect(names).toContain('Data Modelling')
    // Data Governance is shared across both exams.
    expect(names).toContain('Data Governance')
    // An Associate-only domain must NOT appear under Professional.
    expect(names).not.toContain('Databricks Intelligence Platform')
  })

  it('resets the selected domain when the exam changes', async () => {
    renderPage()
    // Pick an Associate domain, then switch exams.
    fireEvent.change(screen.getByLabelText('Domain'), {
      target: { value: 'Governance and Security' },
    })
    expect(screen.getByLabelText('Domain')).toHaveValue('Governance and Security')

    fireEvent.change(screen.getByLabelText('Exam'), {
      target: { value: 'professional' },
    })
    // Domain selection is cleared back to "All domains".
    expect(screen.getByLabelText('Domain')).toHaveValue('')
  })

  it('passes the selected exam to the count and session calls', async () => {
    renderPage()
    fireEvent.change(screen.getByLabelText('Exam'), {
      target: { value: 'professional' },
    })

    await waitFor(() =>
      expect(api.getExerciseCount).toHaveBeenCalledWith({
        exam: 'professional',
        domain: undefined,
        difficulty: undefined,
      })
    )

    fireEvent.click(screen.getByRole('button', { name: /Start Session/i }))
    await waitFor(() =>
      expect(api.getSession).toHaveBeenCalledWith({
        exam: 'professional',
        domain: undefined,
        difficulty: undefined,
      })
    )
  })
})
