/**
 * Shared constants for the study app.
 * Domain/exam values MUST match the backend enums (app/models.py).
 */

/** Exam types (matches backend ExamType). */
export const EXAMS = {
  ASSOCIATE: 'associate',
  PROFESSIONAL: 'professional',
}

/** Default exam when none is selected — never silently mix the two corpora. */
export const DEFAULT_EXAM = EXAMS.ASSOCIATE

/**
 * ~70% pass-bar heuristic (FR-25/FR-27). Surfaced as study guidance — NOT a
 * guarantee of passing the real certification. Mirrors the backend
 * READINESS_THRESHOLD and the ReadinessIndicator fallback.
 */
export const PASS_THRESHOLD = 0.7

/**
 * Domains scoped per exam (matches backend Domain enum).
 * Associate has 7 sections (May 2026 blueprint); Professional has 10 (2026 blueprint).
 * The two exams use independent taxonomies; "Data Governance" is Professional-only.
 */
export const DOMAINS_BY_EXAM = {
  [EXAMS.ASSOCIATE]: [
    'Databricks Intelligence Platform',
    'Data Ingestion and Loading',
    'Data Transformation and Modeling',
    'Working with Lakeflow Jobs',
    'Implementing CI/CD',
    'Troubleshooting, Monitoring, and Optimization',
    'Governance and Security',
  ],
  [EXAMS.PROFESSIONAL]: [
    'Developing Code for Data Processing',
    'Data Ingestion & Acquisition',
    'Data Transformation, Cleansing, and Quality',
    'Data Sharing and Federation',
    'Monitoring and Alerting',
    'Cost & Performance Optimization',
    'Ensuring Data Security and Compliance',
    'Debugging and Deploying',
    'Data Modelling',
    'Data Governance',
  ],
}

/**
 * Back-compat flat list of the default exam's domains.
 * Prefer DOMAINS_BY_EXAM[exam] for exam-scoped UIs.
 */
export const DOMAINS = DOMAINS_BY_EXAM[DEFAULT_EXAM]

export const DIFFICULTIES = ['easy', 'medium', 'hard']

export const EXERCISE_TYPES = {
  SINGLE_CHOICE: 'single_choice',
  MULTI_CHOICE: 'multi_choice',
  CODE_COMPLETION: 'code_completion',
}
