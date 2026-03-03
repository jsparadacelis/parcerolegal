import type { Source } from '@/lib/types'

interface SourceCardProps {
  source: Source
}

export function SourceCard({ source }: SourceCardProps) {
  const styleByType = {
    constitución: 'border-terra/20 bg-terra-light',
    sentencia: 'border-ok/30 bg-ok-light',
  }

  const similarityPercent = Math.round(source.similarity * 100)

  return (
    <div className={`rounded-lg border p-4 ${styleByType[source.type]}`}>
      <div className="mb-2 flex items-start justify-between">
        <h4 className="text-sm font-semibold text-ink">
          {source.title}
        </h4>
        <span className="ml-2 shrink-0 text-xs text-ink-3">
          {similarityPercent}%
        </span>
      </div>

      <p
        data-testid="source-excerpt"
        className="line-clamp-3 text-sm text-ink-2"
      >
        {source.excerpt}
      </p>
    </div>
  )
}
