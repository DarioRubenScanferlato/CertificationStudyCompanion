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
  })

  it('lists all five domains and difficulties', () => {
    renderPage()
    expect(screen.getByRole('option', { name: 'Databricks Lakehouse Platform' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Data Governance' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Easy' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Hard' })).toBeInTheDocument()
  })

  it('fetches exercises with the chosen filters on Start', async () => {
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
