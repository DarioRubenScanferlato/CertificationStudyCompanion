import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useEffect } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
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
function Harness({ exercises }) {
  const { view, startSession } = useSession()
  useEffect(() => {
    startSession(exercises)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  if (view === 'practice') return <MCQPractice />
  if (view === 'summary') return <Summary />
  return null
}

function renderFlow(exercises = EXERCISES) {
  return render(
    <SessionProvider>
      <Harness exercises={exercises} />
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
    expect(api.submitFeedback).toHaveBeenCalledWith({
      exerciseId: 'q1',
      displayedOptionIds: ['a', 'b', 'c', 'd'],
      selectedId: 'a',
    })
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
})
