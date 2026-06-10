/**
 * Positional (Wordle-style) feedback engine for the Code-Completion drill
 * (Story 4.8, FR-14/FR-16, NFR-1). CHARACTER-level (per-letter) — revised
 * 2026-06-10, reversing the earlier token-level design (decision-log #54):
 * every answer is a single fill-in-the-blank word, so token-level feedback was
 * binary (all-green/all-grey); per-letter feedback restores the guess-and-narrow
 * loop. There is intentionally NO server endpoint and NO tokenizer — grading is a
 * per-character comparison in the browser, < 100ms.
 *
 * Contract:
 *   computeFeedback(attempt, canonical, language, { accepted, caseSensitive, ignoreWhitespace })
 *     -> { tokens: Array<{ token, color, position }>, solved: boolean }
 *
 *   tokens are aligned to the ATTEMPT's characters (one entry per character;
 *   when `ignoreWhitespace`, whitespace characters are dropped and so do not
 *   appear as tiles). `token` is the single character as typed — its casing is
 *   preserved for display even when the comparison is case-insensitive.
 *   color ∈ { 'green', 'yellow', 'grey' }
 *     green  — correct letter in the correct position
 *     yellow — letter is in the answer, but in the wrong position
 *     grey   — letter not in the answer
 *   solved — the attempt equals a candidate exactly (all-green AND equal length,
 *            after the case/whitespace rules).
 *
 * Accepted alternatives (FR-16): the target set is `[canonical, ...accepted]`;
 * the attempt is scored against each and the BEST result is returned (most
 * greens, then yellows; a solved candidate always wins).
 */
import { LANGUAGE_ALIASES } from './language'

// Effective case rule: honor an explicit boolean; otherwise default by language
// (Python/PySpark identifiers case-sensitive; SQL case-insensitive).
function effectiveCaseSensitive(language, caseSensitive) {
  if (typeof caseSensitive === 'boolean') return caseSensitive
  return LANGUAGE_ALIASES[String(language || '').toLowerCase()] === 'python'
}

// Split into comparison characters. Non-semantic whitespace is dropped when
// ignoreWhitespace (the rendered tiles then omit spaces — fine for one word).
function toChars(s, ignoreWhitespace) {
  const arr = Array.from(String(s ?? ''))
  return ignoreWhitespace ? arr.filter((c) => !/\s/.test(c)) : arr
}

function norm(ch, caseSensitive) {
  return caseSensitive ? ch : ch.toLowerCase()
}

/** Two-pass Wordle classification of the attempt's chars against ONE candidate. */
function scoreAgainst(attemptChars, targetChars, caseSensitive) {
  const colors = new Array(attemptChars.length).fill('grey')

  // Multiset of remaining target chars (normalized) for yellow accounting.
  const remaining = new Map()
  for (const c of targetChars) {
    const k = norm(c, caseSensitive)
    remaining.set(k, (remaining.get(k) || 0) + 1)
  }

  // Pass 1 — greens by position.
  let greens = 0
  for (let i = 0; i < attemptChars.length; i += 1) {
    if (i >= targetChars.length) continue
    const a = norm(attemptChars[i], caseSensitive)
    const b = norm(targetChars[i], caseSensitive)
    if (a === b) {
      colors[i] = 'green'
      remaining.set(a, remaining.get(a) - 1)
      greens += 1
    }
  }

  // Pass 2 — yellows from whatever target chars remain, else grey.
  let yellows = 0
  for (let i = 0; i < attemptChars.length; i += 1) {
    if (colors[i] === 'green') continue
    const a = norm(attemptChars[i], caseSensitive)
    if ((remaining.get(a) || 0) > 0) {
      colors[i] = 'yellow'
      remaining.set(a, remaining.get(a) - 1)
      yellows += 1
    }
  }

  const tokens = attemptChars.map((c, i) => ({ token: c, color: colors[i], position: i }))
  const solved =
    attemptChars.length === targetChars.length &&
    attemptChars.length > 0 &&
    colors.every((c) => c === 'green')

  return { tokens, greens, yellows, solved }
}

/**
 * Compute per-character feedback for an attempt against the canonical answer and
 * any accepted alternatives.
 * @returns {{ tokens: Array<{token,color,position}>, solved: boolean }}
 */
export function computeFeedback(attempt, canonical, language, options = {}) {
  const { accepted = [], caseSensitive, ignoreWhitespace = true } = options
  const cs = effectiveCaseSensitive(language, caseSensitive)

  const attemptChars = toChars(attempt, ignoreWhitespace)
  const candidates = [canonical, ...(Array.isArray(accepted) ? accepted : [])].filter(
    (c) => typeof c === 'string' && c.length > 0
  )

  let best = null
  for (const cand of candidates) {
    const scored = scoreAgainst(attemptChars, toChars(cand, ignoreWhitespace), cs)
    if (best === null) {
      best = scored
      continue
    }
    if (scored.solved && !best.solved) {
      best = scored
    } else if (scored.solved === best.solved) {
      if (
        scored.greens > best.greens ||
        (scored.greens === best.greens && scored.yellows > best.yellows)
      ) {
        best = scored
      }
    }
  }

  // No usable candidate (e.g. empty canonical): everything grey.
  if (best === null) {
    best = {
      tokens: attemptChars.map((c, i) => ({ token: c, color: 'grey', position: i })),
      solved: false,
    }
  }

  return { tokens: best.tokens, solved: best.solved }
}

export default computeFeedback
