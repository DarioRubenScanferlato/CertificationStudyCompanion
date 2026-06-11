import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import SeenIndicator from './SeenIndicator'

const LABEL = "You've attempted this exercise before"

describe('SeenIndicator', () => {
  it('renders the grey eye with an accessible label and tooltip when seen', () => {
    render(<SeenIndicator seen={true} />)
    // Accessible name available to screen readers (sr-only text).
    expect(screen.getByText(LABEL)).toBeInTheDocument()
    // Native hover tooltip carries the same text.
    expect(screen.getByTitle(LABEL)).toBeInTheDocument()
    // Decorative grey styling on the wrapper.
    expect(screen.getByTestId('seen-indicator').className).toMatch(/text-gray-400/)
  })

  it('renders nothing when not seen', () => {
    const { container } = render(<SeenIndicator seen={false} />)
    expect(container).toBeEmptyDOMElement()
    expect(screen.queryByText(LABEL)).not.toBeInTheDocument()
  })

  it('renders nothing when seen is undefined', () => {
    const { container } = render(<SeenIndicator />)
    expect(container).toBeEmptyDOMElement()
  })
})
