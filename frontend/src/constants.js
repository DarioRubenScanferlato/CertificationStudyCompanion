/**
 * Shared constants for the study app.
 * Domain values MUST match the backend Domain enum (app/models.py).
 */

export const DOMAINS = [
  'Databricks Lakehouse Platform',
  'ELT with Spark SQL and Python',
  'Incremental Data Processing',
  'Production Pipelines',
  'Data Governance',
]

export const DIFFICULTIES = ['easy', 'medium', 'hard']

export const EXERCISE_TYPES = {
  SINGLE_CHOICE: 'single_choice',
  MULTI_CHOICE: 'multi_choice',
  CODE_COMPLETION: 'code_completion',
}
