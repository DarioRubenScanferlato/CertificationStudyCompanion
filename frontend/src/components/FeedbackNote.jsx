import { useState } from 'react'
import { submitExerciseFeedback } from '../api'
import { FOCUS_RING, FOCUS_RING_NEUTRAL } from '../styles/ui'

/**
 * "Flag / leave a note" affordance (Story 11.1, FR-32). A subordinate control on
 * the practice surface that lets the learner attach a free-text note to the
 * current question; the note is persisted server-side to the sidecar feedback
 * file. Shared by the MCQ and Code-Completion runners.
 *
 * Deliberately low-key so it never competes with the primary study actions
 * (Submit / Next). Collapsed by default; expands to a small textarea.
 *
 * @param {object} props
 * @param {string} props.exerciseId
 */
export default function FeedbackNote({ exerciseId }) {
  const [open, setOpen] = useState(false)
  const [note, setNote] = useState('')
  const [status, setStatus] = useState('idle') // idle | saving | saved | error
  const [error, setError] = useState(null)

  const canSubmit = note.trim().length > 0 && status !== 'saving'

  async function handleSubmit() {
    if (!canSubmit) return
    setStatus('saving')
    setError(null)
    try {
      await submitExerciseFeedback({ exerciseId, note: note.trim() })
      setStatus('saved')
      setNote('')
      setOpen(false)
    } catch (e) {
      setStatus('error')
      setError(e?.message || 'Could not save your feedback. Please try again.')
    }
  }

  if (!open) {
    return (
      <div className="mt-3">
        <button
          type="button"
          onClick={() => {
            setOpen(true)
            setStatus('idle')
          }}
          className={`text-xs text-gray-500 hover:text-gray-700 underline underline-offset-2 rounded ${FOCUS_RING_NEUTRAL}`}
        >
          Flag a problem with this question
        </button>
        {status === 'saved' && (
          <span role="status" className="ml-2 text-xs text-green-700">
            Thanks — your note was saved.
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="mt-3 bg-gray-50 border border-gray-200 rounded-lg p-3">
      <label htmlFor={`fb-${exerciseId}`} className="block text-xs font-medium text-gray-700 mb-1">
        What&apos;s wrong with this question? (saved for the author to fix)
      </label>
      <textarea
        id={`fb-${exerciseId}`}
        value={note}
        onChange={(e) => setNote(e.target.value)}
        rows={3}
        maxLength={2000}
        placeholder="e.g. two options are basically the same, or the explanation is outdated…"
        className={`w-full border border-gray-300 rounded px-3 py-2 text-sm ${FOCUS_RING}`}
      />
      {error && (
        <p role="alert" className="mt-1 text-xs text-red-700">
          {error}
        </p>
      )}
      <div className="mt-2 flex items-center gap-2">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!canSubmit}
          className={`text-xs px-3 py-1.5 rounded bg-databricks-500 hover:bg-databricks-600 disabled:opacity-50 text-white font-medium transition-colors ${FOCUS_RING}`}
        >
          {status === 'saving' ? 'Saving…' : 'Submit feedback'}
        </button>
        <button
          type="button"
          onClick={() => {
            setOpen(false)
            setError(null)
          }}
          className={`text-xs px-3 py-1.5 rounded border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition-colors ${FOCUS_RING_NEUTRAL}`}
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
