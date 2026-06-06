import { describe, it, expect } from 'vitest'
import { computeResults } from './Summary'

const EXERCISES = [
  { exerciseId: 'q1', domain: 'Data Governance' },
  { exerciseId: 'q2', domain: 'Data Governance' },
  { exerciseId: 'q3', domain: 'Production Pipelines' },
]

describe('computeResults', () => {
  it('totals correct answers across the session', () => {
    const feedback = {
      q1: { correct: true },
      q2: { correct: false },
      q3: { correct: true },
    }
    const r = computeResults(EXERCISES, feedback)
    expect(r.correct).toBe(2)
    expect(r.answered).toBe(3)
    expect(r.total).toBe(3)
  })

  it('breaks results down per domain', () => {
    const feedback = {
      q1: { correct: true },
      q2: { correct: false },
      q3: { correct: true },
    }
    const r = computeResults(EXERCISES, feedback)
    expect(r.byDomain['Data Governance']).toEqual({ correct: 1, total: 2 })
    expect(r.byDomain['Production Pipelines']).toEqual({ correct: 1, total: 1 })
  })

  it('only counts answered exercises', () => {
    const feedback = { q1: { correct: true } }
    const r = computeResults(EXERCISES, feedback)
    expect(r.answered).toBe(1)
    expect(r.correct).toBe(1)
    expect(r.byDomain['Production Pipelines']).toBeUndefined()
  })
})
