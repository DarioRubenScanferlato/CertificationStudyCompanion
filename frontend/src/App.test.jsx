import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App Component', () => {
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
})
