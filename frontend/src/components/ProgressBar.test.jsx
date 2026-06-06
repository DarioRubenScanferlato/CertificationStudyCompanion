import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ProgressBar from './ProgressBar'

describe('ProgressBar', () => {
  it('renders position and the running correct count', () => {
    render(<ProgressBar current={7} total={20} correct={6} />)
    expect(screen.getByText('Question 7 of 20')).toBeInTheDocument()
    expect(screen.getByText('7/20 · 6 correct')).toBeInTheDocument()
  })

  it('exposes progressbar role with aria value attributes', () => {
    render(<ProgressBar current={3} total={10} correct={2} />)
    const bar = screen.getByRole('progressbar')
    expect(bar).toHaveAttribute('aria-valuenow', '3')
    expect(bar).toHaveAttribute('aria-valuemin', '1')
    expect(bar).toHaveAttribute('aria-valuemax', '10')
    expect(bar).toHaveAttribute('aria-valuetext', 'Question 3 of 10, 2 correct')
  })

  it('fills the bar proportionally to current / total', () => {
    const { container } = render(<ProgressBar current={5} total={10} correct={0} />)
    const fill = container.querySelector('[style]')
    expect(fill).toHaveStyle({ width: '50%' })
  })

  it('disables the fill transition under reduced motion', () => {
    const { container } = render(<ProgressBar current={1} total={4} correct={0} />)
    const fill = container.querySelector('[style]')
    expect(fill.className).toMatch(/motion-reduce:transition-none/)
  })
})
