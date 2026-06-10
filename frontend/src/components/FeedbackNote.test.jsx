import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import FeedbackNote from './FeedbackNote'
import * as api from '../api'

vi.mock('../api')

describe('FeedbackNote (Story 11.1, FR-32)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  function open() {
    render(<FeedbackNote exerciseId="dbx-de-0142" />)
    fireEvent.click(screen.getByRole('button', { name: /flag a problem/i }))
  }

  it('is collapsed by default and expands on click', () => {
    render(<FeedbackNote exerciseId="dbx-de-0142" />)
    expect(screen.queryByRole('textbox')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: /flag a problem/i }))
    expect(screen.getByRole('textbox')).toBeInTheDocument()
  })

  it('caps the note length (maxLength)', () => {
    open()
    expect(screen.getByRole('textbox')).toHaveAttribute('maxLength', '2000')
  })

  it('blocks submit until a non-empty note is entered', () => {
    open()
    const submit = screen.getByRole('button', { name: /submit feedback/i })
    expect(submit).toBeDisabled()
    fireEvent.change(screen.getByRole('textbox'), { target: { value: '   ' } })
    expect(submit).toBeDisabled()
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'two options are identical' } })
    expect(submit).not.toBeDisabled()
  })

  it('submits the note via the API with the exercise id', async () => {
    api.submitExerciseFeedback.mockResolvedValue({ note: 'x', created_at: 'now', resolved: false })
    open()
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'explanation is outdated' } })
    fireEvent.click(screen.getByRole('button', { name: /submit feedback/i }))
    await waitFor(() =>
      expect(api.submitExerciseFeedback).toHaveBeenCalledWith({
        exerciseId: 'dbx-de-0142',
        note: 'explanation is outdated',
      })
    )
    // Collapses back with a confirmation.
    expect(await screen.findByText(/thanks/i)).toBeInTheDocument()
  })

  it('surfaces an error when the API fails (note not lost)', async () => {
    api.submitExerciseFeedback.mockRejectedValue(new Error('Network error'))
    open()
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'bad question' } })
    fireEvent.click(screen.getByRole('button', { name: /submit feedback/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/network error/i)
    // still open with the text retained
    expect(screen.getByRole('textbox')).toHaveValue('bad question')
  })
})
