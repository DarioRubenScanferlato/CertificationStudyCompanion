/**
 * Small, unobtrusive "seen before" indicator (Story 7.6).
 *
 * Renders a grey eye icon when `seen` is true, signalling that the learner has
 * already attempted this exercise. Renders nothing otherwise. The signal comes
 * from the per-entry `seen` flag the backend stamps on session entries (derived
 * from the attempt store); it never reveals whether the previous attempt was
 * correct.
 *
 * Accessibility:
 * - The label is exposed both as a native `title` (hover tooltip) and as
 *   visually-hidden text, so pointer and screen-reader users both get it.
 * - The SVG itself is `aria-hidden` (decorative); the text carries the meaning.
 *
 * Props:
 * - seen: boolean — whether this exercise has a recorded attempt
 */
const SEEN_LABEL = "You've attempted this exercise before"

export default function SeenIndicator({ seen }) {
  if (!seen) return null

  return (
    <span
      title={SEEN_LABEL}
      className="inline-flex items-center text-gray-400"
      data-testid="seen-indicator"
    >
      <span className="sr-only">{SEEN_LABEL}</span>
      <svg
        aria-hidden="true"
        viewBox="0 0 24 24"
        className="w-4 h-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    </span>
  )
}
