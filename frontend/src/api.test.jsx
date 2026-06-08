import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { submitFeedback, getMockSession, APIError } from './api'

// Capture the POST body submitFeedback sends so we can assert the optional
// timeTakenMs contract (Story 8.2 / FR-28): present when finite, omitted otherwise.
function mockFetchOk() {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({ success: true, data: { correct: true } }),
  })
  globalThis.fetch = fetchMock
  return fetchMock
}

function bodyOf(fetchMock) {
  return JSON.parse(fetchMock.mock.calls[0][1].body)
}

describe('submitFeedback timeTakenMs contract (Story 8.2)', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })
  afterEach(() => {
    delete globalThis.fetch
  })

  it('includes timeTakenMs when a finite number is provided', async () => {
    const fetchMock = mockFetchOk()
    await submitFeedback({
      exerciseId: 'q1',
      displayedOptionIds: ['a', 'b', 'c', 'd'],
      selectedId: 'a',
      timeTakenMs: 4200,
    })
    expect(bodyOf(fetchMock)).toMatchObject({
      exerciseId: 'q1',
      selectedId: 'a',
      type: 'mcq',
      timeTakenMs: 4200,
    })
  })

  it('omits timeTakenMs when it is absent (back-compat with untracked submits)', async () => {
    const fetchMock = mockFetchOk()
    await submitFeedback({
      exerciseId: 'q1',
      displayedOptionIds: ['a', 'b', 'c', 'd'],
      selectedId: 'a',
    })
    const body = bodyOf(fetchMock)
    expect(body).not.toHaveProperty('timeTakenMs')
    // Still grades — the existing keys are unchanged.
    expect(body).toMatchObject({ exerciseId: 'q1', selectedId: 'a', type: 'mcq' })
  })

  it('omits timeTakenMs when it is not a finite number', async () => {
    const fetchMock = mockFetchOk()
    await submitFeedback({
      exerciseId: 'q1',
      displayedOptionIds: ['a', 'b', 'c', 'd'],
      selectedId: 'a',
      timeTakenMs: NaN,
    })
    expect(bodyOf(fetchMock)).not.toHaveProperty('timeTakenMs')
  })
})

describe('getMockSession (Story 8.4)', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })
  afterEach(() => {
    delete globalThis.fetch
  })

  it('GETs /api/sessions?mode=mock&exam=… and returns entries + durationMinutes', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        success: true,
        data: [{ exerciseId: 'q1', displayedOptions: [] }],
        error: null,
        durationMinutes: 90,
      }),
    })
    globalThis.fetch = fetchMock

    const result = await getMockSession({ exam: 'associate' })
    const calledUrl = fetchMock.mock.calls[0][0]
    expect(calledUrl).toContain('/api/sessions?')
    expect(calledUrl).toContain('mode=mock')
    expect(calledUrl).toContain('exam=associate')
    expect(result.durationMinutes).toBe(90)
    expect(result.entries).toHaveLength(1)
  })

  it('throws APIError when the API reports failure', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ success: false, data: null, error: 'exam is required' }),
    })
    await expect(getMockSession({})).rejects.toBeInstanceOf(APIError)
  })

  it('defaults durationMinutes to null and entries to [] on a malformed payload', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ success: true, data: null, error: null }),
    })
    const result = await getMockSession({ exam: 'associate' })
    expect(result.entries).toEqual([])
    expect(result.durationMinutes).toBeNull()
  })
})
