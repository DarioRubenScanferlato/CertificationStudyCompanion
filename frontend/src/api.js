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
 * Fetch exercises, optionally filtered.
 * @param {object} filters - { domain, difficulty, exam, exercise_type }
 * @returns {Promise<Array>} list of exercise objects
 * @throws {APIError} on network/parse error or when the API reports failure
 */
export async function fetchExercises(filters = {}) {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.append(key, value)
  }
  const query = params.toString()
  const url = `/api/exercises${query ? `?${query}` : ''}`

  const result = await apiRequest(url)
  if (!result.success) {
    throw new APIError(result.error || 'Failed to load exercises', 200, result)
  }
  return result.data
}
