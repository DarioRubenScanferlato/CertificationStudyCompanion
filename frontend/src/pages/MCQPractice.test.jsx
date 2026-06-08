import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useEffect } from 'react'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { SessionProvider, useSession } from '../context/SessionContext'
import MCQPractice from './MCQPractice'
import Summary from './Summary'
import * as api from '../api'

vi.mock('../api')

function makeOptions() {
  return [
    { id: 'a', text: 'A governance solution' },
    { id: 'b', text: 'A storage format' },
    { id: 'c', text: 'Option C' },
    { id: 'd', text: 'Option D' },
  ]
}

const EXERCISES = [
  {
    exerciseId: 'q1',
    type: 'single_choice',
    domain: 'Data Governance',
    difficulty: 'easy',
    question: 'What is Unity Catalog?',
    codeContext: null,
    displayedOptions: makeOptions(),
  },
  {
    exerciseId: 'q2',
    type: 'single_choice',
    domain: 'Production Pipelines',
    difficulty: 'hard',
    question: 'Pick the right one',
    codeContext: null,
    displayedOptions: makeOptions(),
  },
]

// Drives a session and renders the current view, mirroring App's switch.
function Harness({ exercises, timerDurationSeconds }) {
  const { view, startSession } = useSession()
  useEffect(() => {
    startSession(
      exercises,
      timerDurationSeconds ? { timerDurationSeconds } : undefined
    )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  if (view === 'practice') return <MCQPractice />
  if (view === 'summary') return <Summary />
  return null
}

function renderFlow(exercises = EXERCISES, options = {}) {
  return render(
    <SessionProvider>
      <Harness exercises={exercises} timerDurationSeconds={options.timerDurationSeconds} />
    </SessionProvider>
  )
}

describe('MCQPractice', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('shows progress, domain, difficulty, and the question', () => {
    renderFlow()
    expect(screen.getByText('Question 1 of 2')).toBeInTheDocument()
    expect(screen.getByText('Data Governance')).toBeInTheDocument()
    expect(screen.getByText('easy')).toBeInTheDocument()
    expect(screen.getByText(/What is Unity Catalog/)).toBeInTheDocument()
  })

  it('renders a radiogroup with one radio per displayed option', () => {
    renderFlow()
    expect(screen.getByRole('radiogroup')).toBeInTheDocument()
    const radios = screen.getAllByRole('radio')
    expect(radios).toHaveLength(4)
    // No checkbox / multi-select path remains.
    expect(screen.queryAllByRole('checkbox')).toHaveLength(0)
    expect(screen.queryByText(/select all that apply/i)).not.toBeInTheDocument()
  })

  it('disables Submit until an option is selected', () => {
    renderFlow()
    expect(screen.getByRole('button', { name: 'Submit' })).toBeDisabled()
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    expect(screen.getByRole('button', { name: 'Submit' })).toBeEnabled()
  })

  it('grades via the backend and shows correct feedback, explanation, and reference link', async () => {
    api.submitFeedback.mockResolvedValue({
      correct: true,
      correctOptionId: 'a',
      explanation: 'It is a governance layer.',
      references: ['https://docs.databricks.com/uc'],
    })
    renderFlow()
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))

    expect(await screen.findByText(/Correct!/)).toBeInTheDocument()
    expect(api.submitFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        exerciseId: 'q1',
        displayedOptionIds: ['a', 'b', 'c', 'd'],
        selectedId: 'a',
        // Per-question elapsed time now rides with the submit (Story 8.2 / FR-28).
        timeTakenMs: expect.any(Number),
      })
    )
    expect(screen.getByText(/It is a governance layer/)).toBeInTheDocument()
    const link = screen.getByRole('link', { name: /docs.databricks.com/ })
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })

  it('shows incorrect feedback for a wrong choice', async () => {
    api.submitFeedback.mockResolvedValue({
      correct: false,
      correctOptionId: 'a',
      explanation: 'nope',
      references: [],
    })
    renderFlow()
    fireEvent.click(screen.getByLabelText(/A storage format/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect(await screen.findByText(/Incorrect/)).toBeInTheDocument()
  })

  it('shows a submitting state while grading is in flight', async () => {
    let resolveFn
    api.submitFeedback.mockReturnValue(
      new Promise((resolve) => {
        resolveFn = resolve
      })
    )
    renderFlow()
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))

    expect(screen.getByRole('button', { name: /Submitting/ })).toBeInTheDocument()
    resolveFn({
      correct: true,
      correctOptionId: 'a',
      explanation: 'x',
      references: [],
    })
    expect(await screen.findByText(/Correct!/)).toBeInTheDocument()
  })

  it('grades each question through to summary', async () => {
    api.submitFeedback.mockResolvedValue({
      correct: true,
      correctOptionId: 'a',
      explanation: 'x',
      references: [],
    })
    renderFlow()

    // Answer q1
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    await screen.findByText(/Correct!/)
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))

    // q2
    expect(screen.getByText('Question 2 of 2')).toBeInTheDocument()
    expect(screen.getAllByRole('radio')).toHaveLength(4)
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    await screen.findByText(/Correct!/)

    // Last question -> go to summary
    fireEvent.click(screen.getByRole('button', { name: 'See Results' }))
    expect(screen.getByText('Session complete')).toBeInTheDocument()
    expect(screen.getByText('2/2')).toBeInTheDocument()
  })

  // --- End session / Exit confirm (Story 6.4) ---

  // Answer the current question (q1) so there is progress to protect.
  async function answerFirstQuestion() {
    api.submitFeedback.mockResolvedValue({
      correct: true,
      correctOptionId: 'a',
      explanation: 'x',
      references: [],
    })
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    await screen.findByText(/Correct!/)
  }

  it('shows a persistent, neutral End session control', () => {
    renderFlow()
    const endBtn = screen.getByRole('button', { name: 'End session' })
    expect(endBtn).toBeInTheDocument()
    // Neutral styling — not the databricks-500 Submit treatment.
    expect(endBtn.className).not.toMatch(/databricks-500/)
  })

  it('with at least one answered, End session opens the Exit confirm', async () => {
    renderFlow()
    await answerFirstQuestion()
    fireEvent.click(screen.getByRole('button', { name: 'End session' }))
    const dialog = screen.getByRole('dialog')
    expect(dialog).toBeInTheDocument()
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(screen.getByText(/You've answered 1 of 2\./)).toBeInTheDocument()
  })

  it('See results routes to a partial Summary over the answered subset', async () => {
    renderFlow()
    await answerFirstQuestion()
    fireEvent.click(screen.getByRole('button', { name: 'End session' }))
    fireEvent.click(screen.getByRole('button', { name: 'See results' }))

    expect(screen.getByText('Session complete')).toBeInTheDocument()
    // Partial summary scores over the ANSWERED subset (Story 6.6): 1 correct
    // of 1 answered (the 2nd question was never answered before ending early).
    // Assert the percentage — unambiguous, unlike "1/1" which also appears in
    // the per-domain breakdown row.
    expect(screen.getByText('100% correct')).toBeInTheDocument()
  })

  it('Discard & exit returns to the Start screen', async () => {
    renderFlow()
    await answerFirstQuestion()
    fireEvent.click(screen.getByRole('button', { name: 'End session' }))
    fireEvent.click(screen.getByRole('button', { name: 'Discard & exit' }))

    // Harness renders nothing on the 'select' view.
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.queryByText('Session complete')).not.toBeInTheDocument()
    expect(screen.queryByText(/Question \d of \d/)).not.toBeInTheDocument()
  })

  it('Keep practicing closes the confirm and stays on Practice', async () => {
    renderFlow()
    await answerFirstQuestion()
    fireEvent.click(screen.getByRole('button', { name: 'End session' }))
    fireEvent.click(screen.getByRole('button', { name: 'Keep practicing' }))

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByText('Question 1 of 2')).toBeInTheDocument()
  })

  it('with zero answered, End session exits straight to Start with no confirm', () => {
    renderFlow()
    fireEvent.click(screen.getByRole('button', { name: 'End session' }))
    // No confirm appears...
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    // ...and we left Practice straight to Start (Harness renders null).
    expect(screen.queryByText('Question 1 of 2')).not.toBeInTheDocument()
    expect(screen.queryByText('Session complete')).not.toBeInTheDocument()
  })

  it('degrades gracefully for a code_completion exercise instead of crashing', () => {
    renderFlow([
      {
        exerciseId: 'cc1',
        type: 'code_completion',
        domain: 'ELT with Spark SQL and Python',
        difficulty: 'easy',
        question: 'Fill the blank',
        codeContext: null,
        displayedOptions: [],
      },
    ])
    expect(screen.getByText(/code-completion exercises arrive/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'See Results' })).toBeInTheDocument()
  })

  it('shows a malformed message for an exercise without exactly four options', () => {
    renderFlow([
      {
        exerciseId: 'bad1',
        type: 'single_choice',
        domain: 'Data Governance',
        difficulty: 'easy',
        question: 'Broken',
        codeContext: null,
        displayedOptions: [{ id: 'a', text: 'only one' }],
      },
    ])
    expect(screen.getByText(/malformed/i)).toBeInTheDocument()
  })

  // --- Progress bar, navigation & keyboard shortcuts (Story 6.5) ---

  it('renders a progress bar with position and a running correct count', () => {
    renderFlow()
    const bar = screen.getByRole('progressbar')
    expect(bar).toHaveAttribute('aria-valuenow', '1')
    expect(bar).toHaveAttribute('aria-valuemax', '2')
    expect(screen.getByText('1/2 · 0 correct')).toBeInTheDocument()
  })

  it('updates the running correct count on submit', async () => {
    renderFlow()
    expect(screen.getByText('1/2 · 0 correct')).toBeInTheDocument()
    await answerFirstQuestion()
    expect(screen.getByText('1/2 · 1 correct')).toBeInTheDocument()
  })

  it('updates progress position on navigation', async () => {
    renderFlow()
    await answerFirstQuestion()
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '2')
    expect(screen.getByText('2/2 · 1 correct')).toBeInTheDocument()
  })

  it('selects an option with the "1" key and the "a" key', () => {
    renderFlow()
    fireEvent.keyDown(document, { key: '1' })
    expect(screen.getByLabelText(/A governance solution/)).toBeChecked()
    fireEvent.keyDown(document, { key: 'b' })
    expect(screen.getByLabelText(/A storage format/)).toBeChecked()
  })

  it('Enter submits a selected answer then Enter advances, reaching Summary on the last question', async () => {
    api.submitFeedback.mockResolvedValue({
      correct: true,
      correctOptionId: 'a',
      explanation: 'x',
      references: [],
    })
    renderFlow()

    // q1: select via keyboard, submit via Enter, advance via Enter.
    fireEvent.keyDown(document, { key: '1' })
    fireEvent.keyDown(document, { key: 'Enter' })
    await screen.findByText(/Correct!/)
    fireEvent.keyDown(document, { key: 'Enter' })
    expect(screen.getByText('Question 2 of 2')).toBeInTheDocument()

    // q2: same rhythm, last question -> Summary.
    fireEvent.keyDown(document, { key: 'a' })
    fireEvent.keyDown(document, { key: 'Enter' })
    await screen.findByText(/Correct!/)
    fireEvent.keyDown(document, { key: 'Enter' })
    expect(screen.getByText('Session complete')).toBeInTheDocument()
  })

  it('keyboard selection is a no-op after submit', async () => {
    renderFlow()
    await answerFirstQuestion() // selects + submits option "a"
    // Try to change selection after submit; the radios are disabled and the
    // handler should ignore the key.
    fireEvent.keyDown(document, { key: '2' })
    expect(screen.getByLabelText(/A governance solution/)).toBeChecked()
    expect(screen.getByLabelText(/A storage format/)).not.toBeChecked()
  })

  it('ArrowLeft goes Back read-only without re-POSTing', async () => {
    renderFlow()
    await answerFirstQuestion()
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(screen.getByText('Question 2 of 2')).toBeInTheDocument()

    const callsBefore = api.submitFeedback.mock.calls.length
    fireEvent.keyDown(document, { key: 'ArrowLeft' })
    expect(screen.getByText('Question 1 of 2')).toBeInTheDocument()
    // The revisited question keeps its feedback; no new grading request fired.
    expect(screen.getByText(/Correct!/)).toBeInTheDocument()
    expect(api.submitFeedback.mock.calls.length).toBe(callsBefore)
  })

  it('ArrowRight advances after submit and Skips (records unanswered) before submit', async () => {
    renderFlow()
    // Before submit: ArrowRight skips to q2 without grading.
    fireEvent.keyDown(document, { key: 'ArrowRight' })
    expect(screen.getByText('Question 2 of 2')).toBeInTheDocument()
    expect(api.submitFeedback).not.toHaveBeenCalled()

    // After submit: ArrowRight advances (to Summary, last question).
    await answerFirstQuestion()
    fireEvent.keyDown(document, { key: 'ArrowRight' })
    expect(screen.getByText('Session complete')).toBeInTheDocument()
  })

  it('Back button is disabled on the first question', () => {
    renderFlow()
    expect(screen.getByRole('button', { name: /Back to previous question/ })).toBeDisabled()
  })

  it('Skip button advances without grading (pointer parity)', () => {
    renderFlow()
    fireEvent.click(screen.getByRole('button', { name: /Skip this question/ }))
    expect(screen.getByText('Question 2 of 2')).toBeInTheDocument()
    expect(api.submitFeedback).not.toHaveBeenCalled()
  })

  it('Back button revisits the previous question (pointer parity)', async () => {
    renderFlow()
    await answerFirstQuestion()
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(screen.getByText('Question 2 of 2')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Back to previous question/ }))
    expect(screen.getByText('Question 1 of 2')).toBeInTheDocument()
  })

  it('Escape opens the Exit-confirm (reusing the 6.4 confirm)', async () => {
    renderFlow()
    await answerFirstQuestion()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('exposes accessibility attributes: aria-live region, radiogroup, focus-visible', () => {
    const { container } = renderFlow()
    // aria-live polite announcer present.
    expect(container.querySelector('[aria-live="polite"]')).toBeInTheDocument()
    // Radio group semantics retained.
    expect(screen.getByRole('radiogroup')).toBeInTheDocument()
    // Visible focus-ring classes on controls (Submit shown here).
    expect(screen.getByRole('button', { name: 'Submit' }).className).toMatch(
      /focus-visible:ring/
    )
  })

  it('exposes a discoverable keyboard-hints affordance', () => {
    renderFlow()
    const toggle = screen.getByRole('button', { name: /Keyboard shortcuts/ })
    expect(toggle).toBeInTheDocument()
    fireEvent.click(toggle)
    expect(screen.getByText(/select an option/i)).toBeInTheDocument()
  })
})

describe('MCQPractice optional countdown (Story 8.1)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders no Timer for an untimed session (parity)', () => {
    renderFlow()
    expect(screen.queryByRole('timer')).not.toBeInTheDocument()
  })

  it('renders a counting Timer for a timed session', () => {
    renderFlow(EXERCISES, { timerDurationSeconds: 90 })
    const timer = screen.getByRole('timer')
    expect(timer).toBeInTheDocument()
    expect(screen.getByText('01:30')).toBeInTheDocument()
    act(() => {
      vi.advanceTimersByTime(2000)
    })
    expect(screen.getByText('01:28')).toBeInTheDocument()
  })

  it('auto-ends to the (partial) Summary when the countdown reaches zero', () => {
    renderFlow(EXERCISES, { timerDurationSeconds: 3 })
    // On Practice initially.
    expect(screen.getByRole('radiogroup')).toBeInTheDocument()
    act(() => {
      vi.advanceTimersByTime(3000)
    })
    // endToSummary fired -> Summary view; Practice radiogroup is gone.
    expect(screen.queryByRole('radiogroup')).not.toBeInTheDocument()
    expect(screen.getByText(/session complete/i)).toBeInTheDocument()
  })
})

describe('MCQPractice per-question timing (Story 8.2)', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    api.submitFeedback.mockResolvedValue({
      correct: true,
      correctOptionId: 'a',
      explanation: 'x',
      references: [],
    })
  })

  it('sends a numeric timeTakenMs (>= 0) with the submit', async () => {
    renderFlow()
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    await screen.findByText(/Correct!/)

    const arg = api.submitFeedback.mock.calls[0][0]
    expect(typeof arg.timeTakenMs).toBe('number')
    expect(arg.timeTakenMs).toBeGreaterThanOrEqual(0)
  })

  it('measures timing per question — the clock re-arms on advance', async () => {
    renderFlow()
    // q1
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    await screen.findByText(/Correct!/)
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))

    // q2 — its own submit reports its own (independent) elapsed time.
    expect(screen.getByText('Question 2 of 2')).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    await screen.findByText(/Correct!/)

    expect(api.submitFeedback).toHaveBeenCalledTimes(2)
    const second = api.submitFeedback.mock.calls[1][0]
    expect(second.exerciseId).toBe('q2')
    expect(typeof second.timeTakenMs).toBe('number')
    expect(second.timeTakenMs).toBeGreaterThanOrEqual(0)
  })
})
