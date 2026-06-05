import { describe, it, expect } from 'vitest'
import { useEffect } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { SessionProvider, useSession } from '../context/SessionContext'
import MCQPractice from './MCQPractice'
import Summary from './Summary'

const EXERCISES = [
  {
    id: 'q1',
    type: 'single_choice',
    domain: 'Data Governance',
    difficulty: 'easy',
    question: 'What is Unity Catalog?',
    explanation: 'It is a governance layer.',
    references: ['https://docs.databricks.com/uc'],
    options: [
      { id: 'a', text: 'A governance solution', correct: true },
      { id: 'b', text: 'A storage format', correct: false },
    ],
    answer: ['a'],
  },
  {
    id: 'q2',
    type: 'multi_choice',
    domain: 'Production Pipelines',
    difficulty: 'hard',
    question: 'Select valid options',
    explanation: 'A and B are valid.',
    references: [],
    options: [
      { id: 'a', text: 'Option A', correct: true },
      { id: 'b', text: 'Option B', correct: true },
      { id: 'c', text: 'Option C', correct: false },
    ],
    answer: ['a', 'b'],
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
  it('shows progress, domain, difficulty, and the question', () => {
    renderFlow()
    expect(screen.getByText('Question 1 of 2')).toBeInTheDocument()
    expect(screen.getByText('Data Governance')).toBeInTheDocument()
    expect(screen.getByText('easy')).toBeInTheDocument()
    expect(screen.getByText(/What is Unity Catalog/)).toBeInTheDocument()
  })

  it('renders radio buttons for single-choice', () => {
    renderFlow()
    const radios = screen.getAllByRole('radio')
    expect(radios).toHaveLength(2)
  })

  it('disables Submit until an option is selected', () => {
    renderFlow()
    expect(screen.getByRole('button', { name: 'Submit' })).toBeDisabled()
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    expect(screen.getByRole('button', { name: 'Submit' })).toBeEnabled()
  })

  it('shows correct feedback, explanation, and a new-tab reference link', () => {
    renderFlow()
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))

    expect(screen.getByText(/Correct!/)).toBeInTheDocument()
    expect(screen.getByText(/It is a governance layer/)).toBeInTheDocument()
    const link = screen.getByRole('link', { name: /docs.databricks.com/ })
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })

  it('shows incorrect feedback for a wrong choice', () => {
    renderFlow()
    fireEvent.click(screen.getByLabelText(/A storage format/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect(screen.getByText(/Incorrect/)).toBeInTheDocument()
  })

  it('uses checkboxes for multi-choice and grades all-or-nothing through to summary', () => {
    renderFlow()

    // Answer q1 correctly
    fireEvent.click(screen.getByLabelText(/A governance solution/))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))

    // q2 is multi-choice
    expect(screen.getByText('Question 2 of 2')).toBeInTheDocument()
    expect(screen.getAllByRole('checkbox')).toHaveLength(3)

    fireEvent.click(screen.getByLabelText('Option A'))
    fireEvent.click(screen.getByLabelText('Option B'))
    fireEvent.click(screen.getByRole('button', { name: 'Submit' }))
    expect(screen.getByText(/Correct!/)).toBeInTheDocument()

    // Last question -> go to summary
    fireEvent.click(screen.getByRole('button', { name: 'See Results' }))
    expect(screen.getByText('Session complete')).toBeInTheDocument()
    expect(screen.getByText('2/2')).toBeInTheDocument()
  })

  it('degrades gracefully for a code_completion exercise instead of crashing', () => {
    renderFlow([
      {
        id: 'cc1',
        type: 'code_completion',
        domain: 'ELT with Spark SQL and Python',
        difficulty: 'easy',
        question: 'Fill the blank',
        explanation: 'x',
        references: [],
        options: [],
        answer: [],
      },
    ])
    expect(screen.getByText(/code-completion exercises arrive/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'See Results' })).toBeInTheDocument()
  })

  it('shows a malformed message for an exercise with no options', () => {
    renderFlow([
      {
        id: 'bad1',
        type: 'single_choice',
        domain: 'Data Governance',
        difficulty: 'easy',
        question: 'Broken',
        explanation: 'x',
        references: [],
        options: [],
        answer: [],
      },
    ])
    expect(screen.getByText(/malformed/i)).toBeInTheDocument()
  })
})
