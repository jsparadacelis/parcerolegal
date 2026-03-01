import type { Source } from '@/lib/types'

interface SourceCardProps {
  source: Source
}

export function SourceCard({ source }: SourceCardProps) {
  const styleByType = {
    constitución: 'border-sky-500/30 bg-sky-500/5',
    sentencia: 'border-purple-500/30 bg-purple-500/5',
  }

  const similarityPercent = Math.round(source.similarity * 100)

  return (
    <div className={`rounded-lg border p-4 ${styleByType[source.type]}`}>
      <div className="mb-2 flex items-start justify-between">
        <h4 className="text-sm font-semibold text-slate-200">
          {source.title}
        </h4>
        <span className="ml-2 shrink-0 text-xs text-slate-400">
          {similarityPercent}%
        </span>
      </div>

      <p
        data-testid="source-excerpt"
        className="line-clamp-3 text-sm text-slate-400"
      >
        {source.excerpt}
      </p>
    </div>
  )
}
