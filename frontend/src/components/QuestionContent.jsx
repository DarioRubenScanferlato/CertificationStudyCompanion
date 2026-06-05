import CodeBlock from './CodeBlock'

// Matches fenced code blocks: ```lang\n ... \n```  (language optional, CRLF ok)
const FENCE_RE = /```(\w+)?\r?\n([\s\S]*?)```/g

/**
 * Split question text into alternating prose and fenced-code segments.
 * Returns an array of { type: 'text' | 'code', content, language? }.
 */
export function parseQuestion(input) {
  const text = String(input ?? '')
  const segments = []
  let lastIndex = 0
  let match

  FENCE_RE.lastIndex = 0
  while ((match = FENCE_RE.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: 'text', content: text.slice(lastIndex, match.index) })
    }
    segments.push({
      type: 'code',
      language: match[1] || 'sql',
      content: match[2].replace(/\r?\n$/, ''),
    })
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < text.length) {
    segments.push({ type: 'text', content: text.slice(lastIndex) })
  }
  return segments
}

/**
 * Render question text, highlighting any fenced code blocks with Prism while
 * preserving prose. Prose whitespace/newlines are preserved.
 */
export default function QuestionContent({ text }) {
  const segments = parseQuestion(text || '')

  return (
    <div className="space-y-3">
      {segments.map((seg, i) =>
        seg.type === 'code' ? (
          <CodeBlock key={i} code={seg.content} language={seg.language} />
        ) : (
          <p key={i} className="whitespace-pre-wrap text-gray-900">
            {seg.content.trim()}
          </p>
        )
      )}
    </div>
  )
}
