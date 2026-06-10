/**
 * Shared UI style tokens for the practice runners (MCQ + Code-Completion), so a
 * restyle happens in one place instead of drifting across both pages.
 */

// Difficulty chip palette (easy/medium/hard).
export const DIFFICULTY_STYLES = {
  easy: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800',
  hard: 'bg-red-100 text-red-800',
}

// Focus ring shared by every primary interactive control on the Practice surface.
export const FOCUS_RING =
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-databricks-500 focus-visible:ring-offset-1'

// Neutral focus ring for subordinate controls (e.g. End-session) — visually
// distinct from the primary databricks-500 actions (Story 6.4).
export const FOCUS_RING_NEUTRAL =
  'focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-500 focus-visible:ring-offset-1'
