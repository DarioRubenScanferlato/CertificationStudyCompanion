import { describe, it, expect, vi } from 'vitest'
import { useState } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import ConfirmDialog from './ConfirmDialog'

const ACTIONS = [
  { label: 'See results', onClick: () => {}, variant: 'primary' },
  { label: 'Discard & exit', onClick: () => {}, variant: 'danger' },
  { label: 'Keep practicing', onClick: () => {}, variant: 'neutral' },
]

function renderDialog(props = {}) {
  return render(
    <ConfirmDialog
      open
      title="End this session?"
      description="You've answered 2 of 5."
      actions={ACTIONS}
      onDismiss={() => {}}
      {...props}
    />
  )
}

describe('ConfirmDialog', () => {
  it('renders nothing when closed', () => {
    renderDialog({ open: false })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('renders a labelled, described, modal dialog when open', () => {
    renderDialog()
    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    // Labelled by the title and described by the count copy.
    expect(dialog).toHaveAccessibleName('End this session?')
    expect(dialog).toHaveAccessibleDescription("You've answered 2 of 5.")
  })

  it('renders the actions in EXPERIENCE order', () => {
    renderDialog()
    const buttons = screen.getAllByRole('button')
    expect(buttons.map((b) => b.textContent)).toEqual([
      'See results',
      'Discard & exit',
      'Keep practicing',
    ])
  })

  it('calls the matching onClick when an action is activated', () => {
    const onClick = vi.fn()
    renderDialog({
      actions: [{ label: 'See results', onClick, variant: 'primary' }],
    })
    fireEvent.click(screen.getByRole('button', { name: 'See results' }))
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('calls onDismiss on Escape', () => {
    const onDismiss = vi.fn()
    renderDialog({ onDismiss })
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('calls onDismiss on backdrop click but not on inner click', () => {
    const onDismiss = vi.fn()
    renderDialog({ onDismiss })
    fireEvent.click(screen.getByRole('dialog'))
    expect(onDismiss).not.toHaveBeenCalled()
    fireEvent.click(screen.getByTestId('confirm-dialog-backdrop'))
    expect(onDismiss).toHaveBeenCalledTimes(1)
  })

  it('moves focus into the dialog on open', () => {
    renderDialog()
    // First focusable action receives focus.
    expect(screen.getByRole('button', { name: 'See results' })).toHaveFocus()
  })

  it('traps Tab focus within the dialog', () => {
    renderDialog()
    const dialog = screen.getByRole('dialog')
    const last = screen.getByRole('button', { name: 'Keep practicing' })
    const first = screen.getByRole('button', { name: 'See results' })

    // Tab from the last focusable wraps to the first.
    last.focus()
    fireEvent.keyDown(dialog, { key: 'Tab' })
    expect(first).toHaveFocus()

    // Shift+Tab from the first wraps to the last.
    first.focus()
    fireEvent.keyDown(dialog, { key: 'Tab', shiftKey: true })
    expect(last).toHaveFocus()
  })

  it('restores focus to the trigger element on close', () => {
    function Wrapper() {
      const [open, setOpen] = useState(false)
      return (
        <>
          <button type="button" onClick={() => setOpen(true)}>
            Open
          </button>
          <ConfirmDialog
            open={open}
            title="End this session?"
            description="x"
            actions={[
              { label: 'Keep practicing', onClick: () => setOpen(false), variant: 'neutral' },
            ]}
            onDismiss={() => setOpen(false)}
          />
        </>
      )
    }
    render(<Wrapper />)
    const trigger = screen.getByRole('button', { name: 'Open' })
    trigger.focus()
    fireEvent.click(trigger)

    // Dialog opened and took focus.
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Keep practicing' }))

    // Closed and focus returned to the trigger.
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(trigger).toHaveFocus()
  })
})
