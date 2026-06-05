import { useMemo } from 'react'
import Prism from 'prismjs'
import 'prismjs/components/prism-sql'
import 'prismjs/components/prism-python'
import 'prismjs/themes/prism.css'

// Map our content language tags to Prism grammar names.
const LANGUAGE_ALIASES = {
  sql: 'sql',
  python: 'python',
  py: 'python',
  pyspark: 'python',
}

/**
 * Render a code snippet with Prism.js syntax highlighting. Whitespace and
 * indentation are preserved via <pre>. Falls back to plain (clike) highlighting
 * when the language is unknown.
 */
export default function CodeBlock({ code, language = 'sql' }) {
  const grammarName = LANGUAGE_ALIASES[language?.toLowerCase()] || 'clike'

  const html = useMemo(() => {
    const grammar = Prism.languages[grammarName] || Prism.languages.clike
    return Prism.highlight(code ?? '', grammar, grammarName)
  }, [code, grammarName])

  return (
    <pre
      className={`language-${grammarName} overflow-x-auto rounded bg-gray-50 p-4 text-sm border border-gray-200`}
      data-testid="code-block"
    >
      <code
        className={`language-${grammarName}`}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </pre>
  )
}
