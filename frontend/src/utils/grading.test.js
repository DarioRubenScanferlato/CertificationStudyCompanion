import { describe, it, expect } from 'vitest'
import { gradeAnswer } from './grading'

describe('gradeAnswer', () => {
  it('marks a correct single answer', () => {
    expect(gradeAnswer(['a'], ['a'])).toBe(true)
  })

  it('marks a wrong single answer', () => {
    expect(gradeAnswer(['b'], ['a'])).toBe(false)
  })

  it('is order-independent for multi-select', () => {
    expect(gradeAnswer(['b', 'a'], ['a', 'b'])).toBe(true)
  })

  it('requires all correct options (all-or-nothing)', () => {
    expect(gradeAnswer(['a'], ['a', 'b'])).toBe(false)
  })

  it('rejects extra selections', () => {
    expect(gradeAnswer(['a', 'b', 'c'], ['a', 'b'])).toBe(false)
  })

  it('handles empty selection', () => {
    expect(gradeAnswer([], ['a'])).toBe(false)
  })

  it('handles undefined inputs safely', () => {
    expect(gradeAnswer(undefined, undefined)).toBe(true)
    expect(gradeAnswer(undefined, ['a'])).toBe(false)
  })
})
