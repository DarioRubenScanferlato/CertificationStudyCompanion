import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import FeedbackTokens, { AttemptsCounter, AnswerReveal } from './FeedbackTokens'

describe('FeedbackTokens', () => {
  const tokens = [
    { token: 'SELECT', color: 'green', position: 0 },
    { token: 'x', color: 'yellow', position: 1 },
    { token: 'z', color: 'grey', position: 2 },
  ]

  it('renders each token with a color class AND a non-color cue (color-independence)', () => {
    render(<FeedbackTokens tokens={tokens} />)
    // green token: distinct aria-label + color class
    const green = screen.getByLabelText('SELECT — correct')
    expect(green.className).toMatch(/green/)
    const yellow = screen.getByLabelText('x — wrong position')
    expect(yellow.className).toMatch(/yellow/)
    const grey = screen.getByLabelText('z — not in answer')
    expect(grey.className).toMatch(/gray/)
    // color-independence: the cue differs by more than a class — labels differ.
    expect(green.getAttribute('aria-label')).not.toBe(grey.getAttribute('aria-label'))
  })

  it('exposes a role="status" summary reflecting the counts', () => {
    render(<FeedbackTokens tokens={tokens} />)
    expect(screen.getByRole('status')).toHaveTextContent('1 correct, 1 misplaced, 1 not in answer')
  })

  it('renders the legend only when showLegend is set', () => {
    const { rerender } = render(<FeedbackTokens tokens={tokens} />)
    expect(screen.queryByLabelText('Feedback legend')).toBeNull()
    rerender(<FeedbackTokens tokens={tokens} showLegend />)
    expect(screen.getByLabelText('Feedback legend')).toBeInTheDocument()
  })

  it('renders nothing for empty tokens (no crash)', () => {
    const { container } = render(<FeedbackTokens tokens={[]} />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('AttemptsCounter', () => {
  it('renders the supplied value and max', () => {
    const { rerender } = render(<AttemptsCounter attemptsLeft={6} max={6} />)
    expect(screen.getByTestId('cc-attempts-counter')).toHaveTextContent('Attempts left: 6 of 6')
    rerender(<AttemptsCounter attemptsLeft={5} max={6} />)
    expect(screen.getByTestId('cc-attempts-counter')).toHaveTextContent('Attempts left: 5 of 6')
  })
})

describe('AnswerReveal', () => {
  it('is hidden until revealed, then shows the canonical answer', () => {
    const { rerender } = render(<AnswerReveal revealed={false} answer="format" language="python" />)
    expect(screen.queryByTestId('cc-answer-reveal')).toBeNull()
    rerender(<AnswerReveal revealed answer="format" language="python" />)
    const reveal = screen.getByTestId('cc-answer-reveal')
    expect(reveal).toBeInTheDocument()
    expect(reveal).toHaveTextContent('format')
  })
})
