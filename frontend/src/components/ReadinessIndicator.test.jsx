import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import ReadinessIndicator from './ReadinessIndicator'

describe('ReadinessIndicator', () => {
  it('renders a ready overall state with accuracy and "On track"', () => {
    render(
      <ReadinessIndicator
        readiness={{
          overall: { accuracy: 0.82, ready: true, window: 50 },
          byDomain: {},
          threshold: 0.7,
          window: 50,
        }}
      />
    )
    const overall = screen.getByTestId('readiness-overall')
    expect(within(overall).getByText('82%')).toBeInTheDocument()
    expect(screen.getAllByText('On track').length).toBeGreaterThan(0)
  })

  it('renders a not-ready overall state with "Keep practicing"', () => {
    render(
      <ReadinessIndicator
        readiness={{
          overall: { accuracy: 0.55, ready: false, window: 50 },
          byDomain: {},
          threshold: 0.7,
          window: 50,
        }}
      />
    )
    const overall = screen.getByTestId('readiness-overall')
    expect(within(overall).getByText('55%')).toBeInTheDocument()
    expect(screen.getAllByText('Keep practicing').length).toBeGreaterThan(0)
  })

  it('frames readiness as guidance, not a guarantee', () => {
    render(
      <ReadinessIndicator
        readiness={{
          overall: { accuracy: 0.7, ready: true, window: 50 },
          byDomain: {},
          threshold: 0.7,
          window: 50,
        }}
      />
    )
    expect(screen.getByText(/guidance, not a guarantee/i)).toBeInTheDocument()
  })

  it('renders per-domain readiness with ready / not-ready badges', () => {
    render(
      <ReadinessIndicator
        readiness={{
          overall: { accuracy: 0.75, ready: true, window: 50 },
          byDomain: {
            'Data Governance': { accuracy: 0.9, ready: true },
            'Production Pipelines': { accuracy: 0.4, ready: false },
          },
          threshold: 0.7,
          window: 50,
        }}
      />
    )
    const list = screen.getByTestId('readiness-by-domain')
    const governance = within(list).getByTestId('readiness-domain-Data Governance')
    const pipelines = within(list).getByTestId('readiness-domain-Production Pipelines')
    expect(within(governance).getByText('90%')).toBeInTheDocument()
    expect(within(governance).getByText('On track')).toBeInTheDocument()
    expect(within(pipelines).getByText('40%')).toBeInTheDocument()
    expect(within(pipelines).getByText('Keep practicing')).toBeInTheDocument()
  })

  it('falls back to zeros when readiness is missing', () => {
    render(<ReadinessIndicator readiness={null} />)
    const overall = screen.getByTestId('readiness-overall')
    expect(within(overall).getByText('0%')).toBeInTheDocument()
    expect(screen.queryByTestId('readiness-by-domain')).not.toBeInTheDocument()
  })
})
