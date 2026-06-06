import { useEffect, useId, useRef } from 'react'

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'

const VARIANT_CLASSES = {
  primary:
    'bg-databricks-500 hover:bg-databricks-600 text-white border border-transparent',
  danger:
    'bg-white hover:bg-red-50 text-red-700 border border-red-300',
  neutral:
    'bg-white hover:bg-gray-50 text-gray-800 border border-gray-300',
}

/**
 * Accessible confirmation modal.
 *
 * Props:
 * - open: boolean — render nothing when false
 * - title: string — labels the dialog (aria-labelledby)
 * - description: string — describes the dialog (aria-describedby)
 * - actions: Array<{ label, onClick, variant }> — rendered in order
 * - onDismiss: () => void — called on Esc, backdrop click (= cancel)
 *
 * Accessibility:
 * - role="dialog" + aria-modal="true", labelled + described.
 * - Focus moves into the dialog on open (first action), and Tab / Shift+Tab
 *   cycle is trapped among the dialog's focusable elements.
 * - Esc dismisses (= cancel). Backdrop click dismisses; clicks inside do not.
 * - On close, focus is restored to whatever was focused before open.
 */
export default function ConfirmDialog({
  open,
  title,
  description,
  actions = [],
  onDismiss,
}) {
  const dialogRef = useRef(null)
  const previouslyFocused = useRef(null)
  const titleId = useId()
  const descId = useId()

  // Capture the trigger and move focus into the dialog on open; restore focus
  // to the trigger on close/unmount.
  useEffect(() => {
    if (!open) return undefined

    previouslyFocused.current =
      document.activeElement instanceof HTMLElement ? document.activeElement : null

    const node = dialogRef.current
    if (node) {
      const focusables = node.querySelectorAll(FOCUSABLE)
      const first = focusables[0] || node
      first.focus()
    }

    return () => {
      const trigger = previouslyFocused.current
      if (trigger && typeof trigger.focus === 'function') {
        trigger.focus()
      }
    }
  }, [open])

  if (!open) return null

  function handleKeyDown(event) {
    if (event.key === 'Escape') {
      event.stopPropagation()
      onDismiss?.()
      return
    }
    if (event.key !== 'Tab') return

    const node = dialogRef.current
    if (!node) return
    const focusables = Array.from(node.querySelectorAll(FOCUSABLE)).filter(
      (el) => !el.hasAttribute('disabled')
    )
    if (focusables.length === 0) {
      event.preventDefault()
      return
    }
    const first = focusables[0]
    const last = focusables[focusables.length - 1]
    const active = document.activeElement

    if (event.shiftKey) {
      if (active === first || !node.contains(active)) {
        event.preventDefault()
        last.focus()
      }
    } else if (active === last || !node.contains(active)) {
      event.preventDefault()
      first.focus()
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={() => onDismiss?.()}
      data-testid="confirm-dialog-backdrop"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descId}
        onKeyDown={handleKeyDown}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
      >
        <h2 id={titleId} className="text-lg font-semibold text-gray-900">
          {title}
        </h2>
        {description && (
          <p id={descId} className="mt-2 text-sm text-gray-600">
            {description}
          </p>
        )}

        <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
          {actions.map((action) => (
            <button
              key={action.label}
              type="button"
              onClick={action.onClick}
              className={`rounded px-4 py-2 text-sm font-medium transition-colors ${
                VARIANT_CLASSES[action.variant] || VARIANT_CLASSES.neutral
              }`}
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
