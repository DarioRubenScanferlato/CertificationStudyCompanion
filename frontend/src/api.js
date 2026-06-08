/**
 * API utility with error handling
 * Provides a safe wrapper around fetch with proper error handling
 */

export class APIError extends Error {
  constructor(message, status, data) {
    super(message)
    this.name = 'APIError'
    this.status = status
    this.data = data
  }
}

/**
 * Make a request to the API with proper error handling
 * @param {string} url - API endpoint path (e.g., '/api/health')
 * @param {object} options - fetch options
 * @returns {Promise<any>} parsed JSON response
 * @throws {APIError} on network or parse error
 */
export async function apiRequest(url, options = {}) {
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    let data
    try {
      data = await response.json()
    } catch (e) {
      throw new APIError(
        `Invalid JSON response from ${url}`,
        response.status,
        null
      )
    }

    if (!response.ok) {
      throw new APIError(
        data?.error || `API error: ${response.statusText}`,
        response.status,
        data
      )
    }

    return data
  } catch (error) {
    if (error instanceof APIError) {
      throw error
    }
    throw new APIError(
      `Network error: ${error.message}`,
      null,
      null
    )
  }
}

/**
 * Check if backend is available
 * @returns {Promise<boolean>} true if backend responds, false otherwise
 */
export async function isBackendAvailable() {
  try {
    await apiRequest('/api/health')
    return true
  } catch {
    return false
  }
}

/**
 * Start a practice session: fetch a randomized, anti-leak list of questions.
 * The session payload contains NO correct flag / explanation / references —
 * those are revealed only by submitFeedback after the user answers.
 *
 * @param {object} filters - { exam, domain, difficulty }
 * @returns {Promise<Array>} list of session entries, each:
 *   { exerciseId, type, domain, difficulty, question, codeContext,
 *     displayedOptions: [{ id, text } x4] }
 * @throws {APIError} on network/parse error or when the API reports failure
 */
export async function getSession({ exam, domain, difficulty } = {}) {
  const params = new URLSearchParams()
  if (exam) params.append('exam', exam)
  if (domain) params.append('domain', domain)
  if (difficulty) params.append('difficulty', difficulty)
  const query = params.toString()
  const url = `/api/sessions${query ? `?${query}` : ''}`

  const result = await apiRequest(url)
  if (!result.success) {
    throw new APIError(result.error || 'Failed to load session', null, result)
  }
  // Guard against a "successful" response with missing/non-array data so a
  // malformed payload can't corrupt session state downstream.
  return Array.isArray(result.data) ? result.data : []
}

/**
 * Start a full-length, domain-weighted Mock Exam scoped to one exam (FR-27).
 * Calls GET /api/sessions?mode=mock&exam=<exam>. The builder ignores
 * unseen-first (a mock must be representative, may repeat seen), never mixes
 * exams, and stamps the exam's real `durationMinutes` (Associate 90, Pro 120).
 * The response carries `durationMinutes` at the top level (the practice
 * getSession does not) — the runner needs it to seed the countdown.
 *
 * @param {object} args
 * @param {string} args.exam - exam scope ('associate' | 'professional'); required
 * @returns {Promise<{entries: Array, durationMinutes: number|null}>}
 * @throws {APIError} on network/parse error or when the API reports failure
 */
export async function getMockSession({ exam } = {}) {
  const params = new URLSearchParams()
  params.append('mode', 'mock')
  if (exam) params.append('exam', exam)
  const result = await apiRequest(`/api/sessions?${params.toString()}`)
  if (!result.success) {
    throw new APIError(result.error || 'Failed to load mock exam', null, result)
  }
  return {
    entries: Array.isArray(result.data) ? result.data : [],
    durationMinutes:
      typeof result.durationMinutes === 'number' ? result.durationMinutes : null,
  }
}

/**
 * Replay a session from an explicit set of exercise ids (Summary review/replay).
 * Calls POST /api/sessions {exerciseIds}; the backend re-samples options and
 * re-randomizes order on every call, so replays stay fresh (FR-20/21). Unknown
 * ids are dropped server-side. Returns the same session-entry shape as
 * getSession so it can be fed straight into startSession.
 *
 * @param {string[]} exerciseIds - original authored exercise ids to replay
 * @returns {Promise<Array>} list of session entries (same shape as getSession)
 * @throws {APIError} on network/parse error or when the API reports failure
 */
export async function getSessionByIds(exerciseIds) {
  const result = await apiRequest('/api/sessions', {
    method: 'POST',
    body: JSON.stringify({ exerciseIds }),
  })
  if (!result.success) {
    throw new APIError(result.error || 'Failed to load session', null, result)
  }
  // Mirror getSession's guard against a malformed "successful" payload.
  return Array.isArray(result.data) ? result.data : []
}

/**
 * Count the exercises matching the given filters (Start-screen preview).
 * The response is leak-free: it contains only a count, no options/flags.
 *
 * @param {object} filters - { exam, domain, difficulty }
 * @returns {Promise<number>} number of matching exercises (0 if missing/non-number)
 * @throws {APIError} on network/parse error or when the API reports failure
 */
export async function getExerciseCount({ exam, domain, difficulty } = {}) {
  const params = new URLSearchParams()
  if (exam) params.append('exam', exam)
  if (domain) params.append('domain', domain)
  if (difficulty) params.append('difficulty', difficulty)
  const query = params.toString()
  const url = `/api/exercises/count${query ? `?${query}` : ''}`

  const result = await apiRequest(url)
  if (!result.success) {
    throw new APIError(result.error || 'Failed to load match count', null, result)
  }
  const count = result.data?.count
  return typeof count === 'number' ? count : 0
}

/**
 * Grade a single-select answer on the backend.
 *
 * @param {object} args
 * @param {string} args.exerciseId
 * @param {string[]} args.displayedOptionIds - the option ids that were shown
 * @param {string} args.selectedId - the option id the user chose
 * @param {number} [args.timeTakenMs] - per-question elapsed time in ms (FR-28).
 *   Optional/nullable per the backend contract; only sent when a finite number
 *   so untracked submits stay byte-for-byte unchanged.
 * @returns {Promise<{correct, correctOptionId, explanation, references}>}
 * @throws {APIError} on network/parse error or when the API reports failure
 */
export async function submitFeedback({ exerciseId, displayedOptionIds, selectedId, timeTakenMs }) {
  const body = {
    exerciseId,
    displayedOptionIds,
    selectedId,
    type: 'mcq',
  }
  if (Number.isFinite(timeTakenMs)) {
    body.timeTakenMs = timeTakenMs
  }
  const result = await apiRequest('/api/feedback', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  if (!result.success) {
    throw new APIError(result.error || 'Failed to grade answer', null, result)
  }
  return result.data
}

/**
 * Fetch aggregate practice statistics (FR-23): overall + per-Domain accuracy
 * and a dated trend. Scoped to one exam when `exam` is provided so Associate
 * and Professional history never mix.
 *
 * @param {object} args
 * @param {string} [args.exam] - exam scope (e.g. 'associate'); omit for all
 * @returns {Promise<{overall, byDomain, trend}>}
 *   overall: { attempts, correct, accuracy }
 *   byDomain: { [domain]: { attempts, correct, accuracy } }
 *   trend: [{ date, attempts, correct, accuracy }]
 * @throws {APIError} on network/parse error or when the API reports failure
 */
export async function getStats({ exam } = {}) {
  const params = new URLSearchParams()
  if (exam) params.append('exam', exam)
  const query = params.toString()
  const url = `/api/stats${query ? `?${query}` : ''}`

  const result = await apiRequest(url)
  if (!result.success) {
    throw new APIError(result.error || 'Failed to load stats', null, result)
  }
  return result.data
}

/**
 * Fetch readiness guidance (FR-25): overall readiness vs the ~70% threshold
 * over a rolling window, plus per-Domain readiness. This is guidance, not a
 * guarantee of passing the real exam.
 *
 * @param {object} args
 * @param {string} [args.exam] - exam scope (e.g. 'associate'); omit for all
 * @returns {Promise<{overall, byDomain, threshold, window}>}
 *   overall: { accuracy, ready, window }
 *   byDomain: { [domain]: { accuracy, ready } }
 *   threshold: number, window: number
 * @throws {APIError} on network/parse error or when the API reports failure
 */
export async function getReadiness({ exam } = {}) {
  const params = new URLSearchParams()
  if (exam) params.append('exam', exam)
  const query = params.toString()
  const url = `/api/readiness${query ? `?${query}` : ''}`

  const result = await apiRequest(url)
  if (!result.success) {
    throw new APIError(result.error || 'Failed to load readiness', null, result)
  }
  return result.data
}
