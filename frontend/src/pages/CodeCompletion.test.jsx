import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useEffect } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { SessionProvider, useSession } from '../context/SessionContext'
import CodeCompletion from './CodeCompletion'
import Summary from './Summary'
import * as api from '../api'
import { CODE_COMPLETION_MAX_ATTEMPTS } from '../constants'

vi.mock('../api')

function ccExercise(overrides = {}) {
  return {
    exerciseId: 'c1',
    type: 'code_completion',
    domain: 'Data Ingestion and Loading',
    difficulty: 'medium',
    language: 'python',
    prompt: 'Fill in the Auto Loader option key',
    template: '.option("cloudFiles.___", "json")',
    answer: 'format',
    accepted: ['format'],
    caseSensitive: true,
    ignoreWhitespace: true,
    explanation: 'Auto Loader uses cloudFiles.format.',
    references: ['https://docs.databricks.com/en/ingestion/auto-loader/options.html'],
    ...overrides,
  }
}

// Routes the current view to the code-completion runner (all test exercises are
// code_completion), or Summary — mirroring App's switch. Exposes a Back control
// so tests can revisit a prior exercise (read-only retention).
function Harness({ exercises }) {
  const { view, startSession, prev } = useSession()
  useEffect(() => {
    startSession(exercises)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  return (
    <>
      <button type="button" onClick={prev}>
        __back
      </button>
      {view === 'practice' ? <CodeCompletion /> : view === 'summary' ? <Summary /> : null}
    </>
  )
}

function renderFlow(exercises) {
  return render(
    <SessionProvider>
      <Harness exercises={exercises} />
    </SessionProvider>
  )
}

function guess(text) {
  fireEvent.change(screen.getByLabelText('Your answer'), { target: { value: text } })
  fireEvent.click(screen.getByRole('button', { name: /Submit guess/i }))
}

describe('CodeCompletion guess loop (Story 4.5)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('decrements attempts and renders a feedback row on each guess', () => {
    renderFlow([ccExercise()])
    expect(screen.getByTestId('cc-attempts-counter')).toHaveTextContent(
      `Attempts left: ${CODE_COMPLETION_MAX_ATTEMPTS} of ${CODE_COMPLETION_MAX_ATTEMPTS}`
    )
    guess('wrong')
    expect(screen.getByTestId('cc-attempts-counter')).toHaveTextContent(
      `Attempts left: ${CODE_COMPLETION_MAX_ATTEMPTS - 1}`
    )
    // a feedback row was rendered
    expect(screen.getByLabelText('Attempt feedback')).toBeInTheDocument()
    // not concluded yet — no reveal
    expect(screen.queryByTestId('cc-answer-reveal')).toBeNull()
  })

  it('concludes immediately on a correct guess (reveal + explanation + Next), without burning all attempts', () => {
    renderFlow([ccExercise()])
    guess('format')
    expect(screen.getByText(/Solved in 1 try/i)).toBeInTheDocument()
    expect(screen.getByTestId('cc-answer-reveal')).toBeInTheDocument()
    expect(screen.getByText('Auto Loader uses cloudFiles.format.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /See Results|Next/i })).toBeInTheDocument()
    // input disabled after conclusion; submit button gone
    expect(screen.getByLabelText('Your answer')).toBeDisabled()
    expect(screen.queryByRole('button', { name: /Submit guess/i })).toBeNull()
  })

  it('accepts a valid alternative answer as solved', () => {
    renderFlow([ccExercise({ answer: 'filter', accepted: ['where'], caseSensitive: false })])
    guess('where')
    expect(screen.getByText(/Solved/i)).toBeInTheDocument()
  })

  it('reveals the answer on exhaustion after MAX wrong guesses and disables input', () => {
    renderFlow([ccExercise()])
    for (let i = 0; i < CODE_COMPLETION_MAX_ATTEMPTS; i += 1) guess('nope')
    expect(screen.getByText(/Out of attempts/i)).toBeInTheDocument()
    expect(screen.getByTestId('cc-answer-reveal')).toBeInTheDocument()
    expect(screen.getByText('Auto Loader uses cloudFiles.format.')).toBeInTheDocument()
    expect(screen.getByLabelText('Your answer')).toBeDisabled()
  })

  it('Next advances to the next exercise and resets per-exercise state', () => {
    renderFlow([ccExercise(), ccExercise({ exerciseId: 'c2', prompt: 'Second prompt', answer: 'json' })])
    guess('format') // solve #1
    fireEvent.click(screen.getByRole('button', { name: /^Next$/i }))
    // advanced to c2
    expect(screen.getByText('Second prompt')).toBeInTheDocument()
    // state reset: full attempts, no history, not concluded
    expect(screen.getByTestId('cc-attempts-counter')).toHaveTextContent(
      `Attempts left: ${CODE_COMPLETION_MAX_ATTEMPTS} of ${CODE_COMPLETION_MAX_ATTEMPTS}`
    )
    expect(screen.queryByLabelText('Attempt feedback')).toBeNull()
    expect(screen.getByRole('button', { name: /Submit guess/i })).toBeInTheDocument()
  })

  it('Next on the last exercise routes to the Summary', () => {
    renderFlow([ccExercise()])
    guess('format')
    fireEvent.click(screen.getByRole('button', { name: /See Results/i }))
    expect(screen.getByText(/Session Complete|Results|Summary/i)).toBeInTheDocument()
  })

  it('never calls the grading API (code-completion is client-side only)', () => {
    renderFlow([ccExercise()])
    guess('wrong')
    guess('format')
    expect(api.submitFeedback).not.toHaveBeenCalled()
  })

  it('retains a concluded drill on Back instead of re-arming it', () => {
    renderFlow([ccExercise(), ccExercise({ exerciseId: 'c2', prompt: 'Second prompt' })])
    guess('format') // solve c1
    fireEvent.click(screen.getByRole('button', { name: /^Next$/i }))
    expect(screen.getByText('Second prompt')).toBeInTheDocument()

    // Go back to c1 — it must show its final solved result, not a fresh loop.
    fireEvent.click(screen.getByRole('button', { name: '__back' }))
    expect(screen.getByText(/Solved in 1 try/i)).toBeInTheDocument()
    expect(screen.getByTestId('cc-answer-reveal')).toBeInTheDocument()
    expect(screen.getByLabelText('Your answer')).toBeDisabled()
    expect(screen.queryByRole('button', { name: /Submit guess/i })).toBeNull()
  })

  it('renders PER-CHARACTER feedback (green/yellow/grey) on a guess (Story 4.8)', () => {
    renderFlow([ccExercise()]) // answer "format"
    guess('wrong') // w,r,o,n,g vs f,o,r,m,a,t
    // One tile per character; 'r' and 'o' are present-but-misplaced (yellow),
    // 'w','n','g' are not in "format" (grey). Proves per-letter, not token-level.
    expect(screen.getByLabelText('r — wrong position')).toBeInTheDocument()
    expect(screen.getByLabelText('o — wrong position')).toBeInTheDocument()
    expect(screen.getByLabelText('w — not in answer')).toBeInTheDocument()
  })

  it('Skip advances to the next exercise WITHOUT revealing the answer', () => {
    renderFlow([ccExercise(), ccExercise({ exerciseId: 'c2', prompt: 'Second prompt' })])
    fireEvent.click(screen.getByRole('button', { name: /^Skip$/i }))
    // advanced to c2; c1's answer was never revealed
    expect(screen.getByText('Second prompt')).toBeInTheDocument()
    expect(screen.queryByTestId('cc-answer-reveal')).toBeNull()
    expect(api.submitFeedback).not.toHaveBeenCalled()
  })

  it('a skipped exercise is not recorded — revisiting it starts fresh', () => {
    renderFlow([ccExercise(), ccExercise({ exerciseId: 'c2', prompt: 'Second prompt' })])
    fireEvent.click(screen.getByRole('button', { name: /^Skip$/i })) // skip c1 -> c2
    fireEvent.click(screen.getByRole('button', { name: '__back' })) // back to c1
    // fresh loop: full attempts, no reveal, still answerable
    expect(screen.getByTestId('cc-attempts-counter')).toHaveTextContent(
      `Attempts left: ${CODE_COMPLETION_MAX_ATTEMPTS} of ${CODE_COMPLETION_MAX_ATTEMPTS}`
    )
    expect(screen.queryByTestId('cc-answer-reveal')).toBeNull()
    expect(screen.getByRole('button', { name: /Submit guess/i })).toBeInTheDocument()
  })
})
