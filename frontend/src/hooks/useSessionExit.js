import { useCallback, useState } from 'react'
import { useSession } from '../context/SessionContext'
import { useRegisterExitConfirm } from '../App'

/**
 * Shared Exit-confirm wiring (Story 6.4) for the practice runners. Owns the
 * confirm-dialog open state, registers the trigger with the header Home
 * affordance, and exposes the three dialog actions. Used by both MCQPractice and
 * CodeCompletion so the flow can't drift between them.
 *
 * @param {object} [opts]
 * @param {boolean} [opts.skipConfirm] - when true, requestExit exits straight to
 *   Start with no prompt (MCQPractice passes `answeredCount === 0`).
 * @returns {{ confirmOpen, requestExit, closeConfirm, handleSeeResults, handleDiscard }}
 */
export function useSessionExit({ skipConfirm = false } = {}) {
  const { endToSummary, reset } = useSession()
  const [confirmOpen, setConfirmOpen] = useState(false)

  const requestExit = useCallback(() => {
    if (skipConfirm) {
      reset()
      return
    }
    setConfirmOpen(true)
  }, [skipConfirm, reset])

  // Let the header Home affordance route through this same flow.
  useRegisterExitConfirm(requestExit)

  const closeConfirm = useCallback(() => setConfirmOpen(false), [])
  const handleSeeResults = useCallback(() => {
    setConfirmOpen(false)
    endToSummary()
  }, [endToSummary])
  const handleDiscard = useCallback(() => {
    setConfirmOpen(false)
    reset()
  }, [reset])

  return { confirmOpen, requestExit, closeConfirm, handleSeeResults, handleDiscard }
}
