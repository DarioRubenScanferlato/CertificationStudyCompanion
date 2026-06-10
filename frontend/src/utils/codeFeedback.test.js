import { describe, it, expect } from 'vitest'
import { computeFeedback } from './codeFeedback'

const colors = (fb) => fb.tokens.map((t) => t.color)
const chars = (fb) => fb.tokens.map((t) => t.token).join('')

describe('computeFeedback — per-character green/yellow/grey (Story 4.8)', () => {
  it('all-correct attempt is all green and solved', () => {
    const fb = computeFeedback('format', 'format', 'python')
    expect(colors(fb)).toEqual(['green', 'green', 'green', 'green', 'green', 'green'])
    expect(fb.solved).toBe(true)
    expect(chars(fb)).toBe('format') // rendered chars preserve what was typed
  })

  it('right letters in the wrong place are yellow', () => {
    // target abc; attempt acb -> a green, c & b present-but-misplaced
    const fb = computeFeedback('acb', 'abc', 'sql')
    expect(colors(fb)).toEqual(['green', 'yellow', 'yellow'])
    expect(fb.solved).toBe(false)
  })

  it('letters not in the answer are grey', () => {
    const fb = computeFeedback('axc', 'abc', 'sql')
    expect(colors(fb)).toEqual(['green', 'grey', 'green'])
  })

  it('applies the two-pass duplicate-letter rule', () => {
    // target abc has a single "a"; attempt "aab": pos0 a green consumes it,
    // pos1 a has none left -> grey; pos2 b -> yellow.
    const fb = computeFeedback('aab', 'abc', 'sql')
    expect(colors(fb)).toEqual(['green', 'grey', 'yellow'])
  })
})

describe('computeFeedback — accepted alternatives (FR-16)', () => {
  it('solves when the attempt matches an accepted alternative', () => {
    const fb = computeFeedback('where', 'filter', 'python', { accepted: ['where'] })
    expect(fb.solved).toBe(true)
    expect(colors(fb).every((c) => c === 'green')).toBe(true)
  })

  it('returns the best-scoring candidate', () => {
    // canonical shares 0 letters in place; accepted is exact -> accepted wins.
    const fb = computeFeedback('json', 'csv', 'sql', { accepted: ['json'] })
    expect(fb.solved).toBe(true)
  })
})

describe('computeFeedback — case rules', () => {
  it('SQL is case-insensitive by default (select == SELECT)', () => {
    const fb = computeFeedback('select', 'SELECT', 'sql')
    expect(colors(fb).every((c) => c === 'green')).toBe(true)
    expect(fb.solved).toBe(true)
  })

  it('PySpark is case-sensitive by default (DF != df)', () => {
    const fb = computeFeedback('DF', 'df', 'python')
    expect(fb.solved).toBe(false)
    expect(colors(fb)).toEqual(['grey', 'grey'])
  })

  it('respects an explicit caseSensitive override', () => {
    const fb = computeFeedback('DF', 'df', 'python', { caseSensitive: false })
    expect(fb.solved).toBe(true)
  })
})

describe('computeFeedback — whitespace, length & perf', () => {
  it('ignores non-semantic whitespace by default', () => {
    const fb = computeFeedback('fo rmat', 'format', 'python')
    expect(fb.solved).toBe(true)
    expect(colors(fb).every((c) => c === 'green')).toBe(true)
  })

  it('a correct prefix is NOT solved (length must match)', () => {
    const fb = computeFeedback('form', 'format', 'python')
    expect(colors(fb)).toEqual(['green', 'green', 'green', 'green'])
    expect(fb.solved).toBe(false) // shorter than the answer
  })

  it('an attempt LONGER than the answer greys the extra trailing chars and is not solved', () => {
    // exercises the `i >= targetChars.length` guard — extras fall through to grey
    const fb = computeFeedback('formatXY', 'format', 'python')
    expect(colors(fb)).toEqual(['green', 'green', 'green', 'green', 'green', 'green', 'grey', 'grey'])
    expect(fb.solved).toBe(false)
  })

  it('marks everything grey (not solved) when the canonical is empty', () => {
    const fb = computeFeedback('abc', '', 'sql')
    expect(colors(fb)).toEqual(['grey', 'grey', 'grey'])
    expect(fb.solved).toBe(false)
  })

  it('computes a realistic word well within the NFR-1 budget', () => {
    const start = performance.now()
    computeFeedback('checkpointLocation', 'checkpointLocation', 'python', { accepted: ['x'] })
    expect(performance.now() - start).toBeLessThan(50)
  })
})
