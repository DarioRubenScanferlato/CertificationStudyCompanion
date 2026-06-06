---
title: DataBricks DE Cert Study Companion — Visual Identity
status: final
created: 2026-06-05
updated: 2026-06-05
sources:
  - ../../prds/prd-DataBricks-DE-cert-study-companion-2026-06-05/prd.md
  - ../../architecture.md
colors:
  brand:
    databricks-50: "#fff1ed"
    databricks-500: "#ff3621"   # Databricks lakehouse orange-red (primary action)
    databricks-600: "#e02e1a"
    databricks-900: "#7a1a10"
  neutral:
    white: "#ffffff"
    gray-100: "#f3f4f6"
    gray-200: "#e5e7eb"
    gray-300: "#d1d5db"
    gray-500: "#6b7280"
    gray-700: "#374151"
    gray-900: "#111827"
  feedback:
    correct-bg: "#dcfce7"      # green-100
    correct-fg: "#166534"      # green-800
    correct-border: "#22c55e"  # green-500
    incorrect-bg: "#fee2e2"    # red-100
    incorrect-fg: "#991b1b"    # red-800
    incorrect-border: "#ef4444"# red-500
    warn-bg: "#fefce8"         # yellow-50/100 (skipped / unsupported)
  difficulty:
    easy: "#dcfce7 / #166534"
    medium: "#fef9c3 / #854d0e"
    hard: "#fee2e2 / #991b1b"
typography:
  family: "system-ui / Tailwind default sans"
  mono: "ui-monospace (code snippets via CodeBlock)"
rounded:
  default: "rounded (0.25rem)"
  card: "rounded-lg (0.5rem)"
spacing:
  page-max: "max-w-7xl header/main; content columns max-w-xl/2xl/3xl"
---

# DataBricks DE Cert Study Companion — Visual Identity

> **Minimal by intent.** Per the user's direction this round, we are not redesigning the look — we are inheriting the visual language already implemented (Tailwind + the `databricks-*` palette) and recording it so EXPERIENCE.md can reference tokens by name. Visual evolution can come in a later UX pass.

## Brand & Style

Clean, exam-serious, low-chrome study tool. White canvas, neutral gray structure, a single warm Databricks accent (`{colors.brand.databricks-500}`) reserved for the primary action on each screen. Feedback color is semantic and unmistakable: green = correct, red = incorrect, yellow = skipped/unsupported. Calm and legible over decorative — the content (questions, code, explanations) is the hero.

## Colors

Inherited from the implemented Tailwind theme (frontmatter `colors`). Accent (`databricks-500`) is the primary CTA and selection highlight; neutrals carry layout and text; the `feedback.*` set is reserved strictly for answer correctness and session-state signals (never decorative). Difficulty chips use the `difficulty.*` pairs.

## Components

Visual component specs are inherited from current implementation; **behavioral** specs live in EXPERIENCE.md › Component Patterns. New QoL surfaces (progress bar, end-session control, confirm dialog, review-incorrect list) should reuse existing tokens — accent for primary action, neutral for secondary, `feedback.*` only for correctness/state.

## Do's and Don'ts

- **Do** keep one accent action per screen; everything else neutral.
- **Do** reserve green/red/yellow for correctness and session state only.
- **Don't** introduce new colors, fonts, or decorative styling in this pass — this round is functional/QoL, not a visual redesign.
