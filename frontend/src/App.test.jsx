import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import App from './App'

describe('App Component', () => {
  it('renders without crashing', () => {
    render(<App />)
    expect(screen.getByText(/Databricks DE Certification Study Companion/i)).toBeInTheDocument()
  })

  it('displays welcome message', () => {
    render(<App />)
    expect(screen.getByText(/Welcome!/i)).toBeInTheDocument()
  })

  it('displays instruction text', () => {
    render(<App />)
    expect(screen.getByText(/Frontend initialized successfully/i)).toBeInTheDocument()
  })
})
