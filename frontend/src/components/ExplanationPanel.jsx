/**
 * Shared post-answer explanation + references panel, used by both the MCQ
 * runner (MCQPractice `Feedback`) and the Code-Completion runner so the markup,
 * link semantics, and a11y stay identical across the two.
 *
 * @param {object} props
 * @param {string} props.explanation - teaching text (whitespace preserved)
 * @param {string[]} [props.references] - reference URLs (open in a new tab)
 */
export default function ExplanationPanel({ explanation, references = [] }) {
  return (
    <div className="mt-4 bg-white border border-gray-200 rounded-lg p-5">
      <h3 className="text-sm font-semibold text-gray-700 mb-1">Explanation</h3>
      <p className="text-gray-800 whitespace-pre-wrap">{explanation}</p>

      {references.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-semibold text-gray-700 mb-1">References</h3>
          <ul className="list-disc list-inside space-y-1">
            {references.map((ref, i) => (
              <li key={`${ref}-${i}`}>
                <a
                  href={ref}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-databricks-500 hover:underline break-all"
                >
                  {ref}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
