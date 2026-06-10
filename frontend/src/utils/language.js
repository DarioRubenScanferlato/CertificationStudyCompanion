/**
 * Single source of truth for the languages the app highlights / compares.
 * Imported by CodeBlock (Prism grammar) and codeFeedback (per-language case
 * rule) so a new language tag is added in exactly one place.
 */
export const LANGUAGE_ALIASES = {
  sql: 'sql',
  python: 'python',
  py: 'python',
  pyspark: 'python',
}

/**
 * Normalize a language tag to its canonical alias, or null if unknown.
 * Callers apply their own fallback (e.g. Prism 'clike' for unknown).
 */
export function normalizeLanguage(language) {
  return LANGUAGE_ALIASES[String(language || '').toLowerCase()] || null
}
