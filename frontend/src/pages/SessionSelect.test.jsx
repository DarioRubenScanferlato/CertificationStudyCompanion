import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { SessionProvider } from '../context/SessionContext'
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

describe('SessionSelect', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    // Default: a non-zero count so the live-count effect never rejects and
    // Start stays enabled unless a test overrides it.
    api.getExerciseCount.mockResolvedValue(10)
  })

  it('lists the Associate domains and difficulties by default', () => {
    renderPage()
    expect(screen.getByRole('option', { name: 'Databricks Lakehouse Platform' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Data Governance' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Easy' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Hard' })).toBeInTheDocument()
  })

  it('fetches exercises with the chosen filters (incl. exam) on Start', async () => {
    api.getSession.mockResolvedValue([{ id: 'q1' }])
    renderPage()

    fireEvent.change(screen.getByLabelText('Domain'), {
      target: { value: 'Data Governance' },
    })
    fireEvent.change(screen.getByLabelText('Difficulty'), {
      target: { value: 'easy' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Start Session/i }))

    await waitFor(() =>
      expect(api.getSession).toHaveBeenCalledWith({
        exam: 'associate',
        domain: 'Data Governance',
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
      target: { value: 'Data Governance' },
    })

    expect(await screen.findByText('7 questions match')).toBeInTheDocument()
    await waitFor(() =>
      expect(api.getExerciseCount).toHaveBeenCalledWith({
        exam: 'associate',
        domain: 'Data Governance',
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

  it('lists exactly the 5 Associate domains (incl. Data Governance) by default', () => {
    renderPage()
    const names = domainOptionNames()
    expect(names).toEqual([
      'Databricks Lakehouse Platform',
      'ELT with Spark SQL and Python',
      'Incremental Data Processing',
      'Production Pipelines',
      'Data Governance',
    ])
    expect(names).toHaveLength(5)
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
    expect(names).not.toContain('Databricks Lakehouse Platform')
  })

  it('resets the selected domain when the exam changes', async () => {
    renderPage()
    // Pick an Associate domain, then switch exams.
    fireEvent.change(screen.getByLabelText('Domain'), {
      target: { value: 'Data Governance' },
    })
    expect(screen.getByLabelText('Domain')).toHaveValue('Data Governance')

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
