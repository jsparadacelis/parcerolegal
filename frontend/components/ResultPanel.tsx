import ReactMarkdown from 'react-markdown'
import type { QueryResponse } from '@/lib/types'
import { SourceCard } from './SourceCard'

interface ResultPanelProps {
  response: QueryResponse
}

export function ResultPanel({ response }: ResultPanelProps) {
  const hasSources = response.sources.length > 0

  return (
    <div className="mt-8">
      {/* Answer */}
      <div className="prose prose-invert mb-6 max-w-none">
        <ReactMarkdown
          components={{
            p: ({ children }) => (
              <p className="mb-4 leading-relaxed text-slate-200">{children}</p>
            ),
            strong: ({ children }) => (
              <strong className="font-semibold text-yellow-500">{children}</strong>
            ),
            em: ({ children }) => (
              <em className="italic text-slate-300">{children}</em>
            ),
          }}
        >
          {response.answer}
        </ReactMarkdown>
      </div>

      {/* Sources */}
      {hasSources && (
        <div className="mt-8">
          <h3 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">
            Fuentes
          </h3>
          <div className="space-y-3">
            {response.sources.map((source, index) => (
              <SourceCard key={index} source={source} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
