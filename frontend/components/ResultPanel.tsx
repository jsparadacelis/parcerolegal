import ReactMarkdown from 'react-markdown'
import type { QueryResponse } from '@/lib/types'
import { SourceCard } from './SourceCard'
import { Disclaimer } from './Disclaimer'

interface ResultPanelProps {
  response: QueryResponse
}

export function ResultPanel({ response }: ResultPanelProps) {
  const hasSources = response.sources.length > 0

  return (
    <div className="mt-8">
      <div className="bg-terra-pale rounded-2xl p-5 border border-terra-border">
        {/* Answer */}
        <div className="mb-4">
          <ReactMarkdown
            components={{
              p: ({ children }) => (
                <p className="mb-4 text-sm leading-relaxed text-ink-2">{children}</p>
              ),
              strong: ({ children }) => (
                <strong className="font-semibold text-ink">{children}</strong>
              ),
              em: ({ children }) => (
                <em className="italic text-ink-3">{children}</em>
              ),
            }}
          >
            {response.answer}
          </ReactMarkdown>
        </div>

        {/* Sources */}
        {hasSources && (
          <div className="mb-4">
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-ink-3">
              Fuentes
            </h3>
            <div className="space-y-3">
              {response.sources.map((source, index) => (
                <SourceCard key={index} source={source} />
              ))}
            </div>
          </div>
        )}

        {/* Disclaimer — siempre al final */}
        <Disclaimer />
      </div>
    </div>
  )
}
