import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { SessionProvider } from '../context/SessionContext'
import StatsDashboard from './StatsDashboard'
import * as api from '../api'

vi.mock('../api')

function renderPage() {
  return render(
    <SessionProvider>
      <StatsDashboard />
    </SessionProvider>
  )
}

const STATS_WITH_HISTORY = {
  overall: { attempts: 20, correct: 15, accuracy: 0.75 },
  byDomain: {
    'Data Governance': { attempts: 10, correct: 9, accuracy: 0.9 },
    'Production Pipelines': { attempts: 10, correct: 4, accuracy: 0.4 },
  },
  trend: [
    { date: '2026-06-01', attempts: 8, correct: 6, accuracy: 0.75 },
    { date: '2026-06-02', attempts: 12, correct: 9, accuracy: 0.75 },
  ],
}

const READINESS = {
  overall: { accuracy: 0.75, ready: true, window: 50 },
  byDomain: {
    'Data Governance': { accuracy: 0.9, ready: true },
    'Production Pipelines': { accuracy: 0.4, ready: false },
  },
  threshold: 0.7,
  window: 50,
}

describe('StatsDashboard', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    api.getStats.mockResolvedValue(STATS_WITH_HISTORY)
    api.getReadiness.mockResolvedValue(READINESS)
  })

  it('renders overall accuracy and attempts from mocked getStats', async () => {
    renderPage()
    expect(await screen.findByTestId('overall-accuracy')).toHaveTextContent('75%')
    expect(screen.getByTestId('overall-attempts')).toHaveTextContent('20')
    expect(api.getStats).toHaveBeenCalledWith({ exam: 'associate' })
  })

  it('renders per-domain accuracy rows', async () => {
    renderPage()
    const list = await screen.findByTestId('stats-by-domain')
    expect(within(list).getByText('Data Governance')).toBeInTheDocument()
    expect(within(list).getByText('Production Pipelines')).toBeInTheDocument()
    expect(within(list).getByText('90%')).toBeInTheDocument()
    expect(within(list).getByText('40%')).toBeInTheDocument()
  })

  it('highlights weak domains (below readiness) and not strong ones', async () => {
    renderPage()
    await screen.findByTestId('stats-by-domain')
    const weak = screen.getByTestId('stats-domain-Production Pipelines')
    const strong = screen.getByTestId('stats-domain-Data Governance')
    expect(weak).toHaveAttribute('data-weak', 'true')
    expect(within(weak).getByText('Needs work')).toBeInTheDocument()
    expect(strong).toHaveAttribute('data-weak', 'false')
  })

  it('renders the trend list', async () => {
    renderPage()
    const trend = await screen.findByTestId('stats-trend')
    expect(within(trend).getByTestId('trend-2026-06-01')).toBeInTheDocument()
    expect(within(trend).getByTestId('trend-2026-06-02')).toBeInTheDocument()
  })

  it('shows an empty-history state when there are no attempts', async () => {
    api.getStats.mockResolvedValue({
      overall: { attempts: 0, correct: 0, accuracy: 0 },
      byDomain: {},
      trend: [],
    })
    api.getReadiness.mockResolvedValue({
      overall: { accuracy: 0, ready: false, window: 50 },
      byDomain: {},
      threshold: 0.7,
      window: 50,
    })
    renderPage()
    expect(await screen.findByTestId('stats-empty')).toHaveTextContent(/no practice history/i)
    expect(screen.queryByTestId('stats-by-domain')).not.toBeInTheDocument()
    expect(screen.queryByTestId('stats-trend')).not.toBeInTheDocument()
  })

  it('shows an error when the request fails', async () => {
    api.getStats.mockRejectedValue(new Error('Network error: down'))
    renderPage()
    expect(await screen.findByRole('alert')).toHaveTextContent(/network error/i)
  })

  it('embeds the readiness indicator', async () => {
    renderPage()
    expect(await screen.findByTestId('readiness-overall')).toBeInTheDocument()
  })
})
