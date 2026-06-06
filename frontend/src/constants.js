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
 * Domains scoped per exam (matches backend Domain enum).
 * Associate has 5 domains; Professional has 10 (2026 blueprint).
 * "Data Governance" is SHARED — it appears in BOTH lists.
 */
export const DOMAINS_BY_EXAM = {
  [EXAMS.ASSOCIATE]: [
    'Databricks Lakehouse Platform',
    'ELT with Spark SQL and Python',
    'Incremental Data Processing',
    'Production Pipelines',
    'Data Governance',
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
