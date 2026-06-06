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
 * @returns {Promise<{correct, correctOptionId, explanation, references}>}
 * @throws {APIError} on network/parse error or when the API reports failure
 */
export async function submitFeedback({ exerciseId, displayedOptionIds, selectedId }) {
  const result = await apiRequest('/api/feedback', {
    method: 'POST',
    body: JSON.stringify({
      exerciseId,
      displayedOptionIds,
      selectedId,
      type: 'mcq',
    }),
  })
  if (!result.success) {
    throw new APIError(result.error || 'Failed to grade answer', null, result)
  }
  return result.data
}
