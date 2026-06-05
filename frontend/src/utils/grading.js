/**
 * Client-side answer grading.
 *
 * The exercise payload already includes the correct answer (the app is a local
 * study tool), so grading happens in the browser for instant feedback.
 */

/**
 * Grade a selection against the correct answer using all-or-nothing scoring:
 * the selected option IDs must exactly match the correct option IDs (order
 * independent). This is the exam-realistic rule for multi-select questions.
 *
 * @param {string[]} selected - option IDs the user chose
 * @param {string[]} correct - the exercise's correct option IDs
 * @returns {boolean} true only if the two sets are exactly equal
 */
export function gradeAnswer(selected, correct) {
  const selectedSet = new Set(selected || [])
  const correctSet = new Set(correct || [])
  // An exercise with no defined correct answer can never be "correct" — this
  // guards malformed data (missing/empty answer) from grading as a pass.
  if (correctSet.size === 0) return false
  if (selectedSet.size !== correctSet.size) return false
  for (const id of selectedSet) {
    if (!correctSet.has(id)) return false
  }
  return true
}
