import type { Source } from '@/lib/types'

interface SourceCardProps {
  source: Source
}

export function SourceCard({ source }: SourceCardProps) {
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 text-xs font-semibold text-terra bg-terra-light border border-terra/12 px-3 py-2 min-h-[36px] rounded-lg hover:opacity-75 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-terra focus-visible:ring-offset-1"
    >
      {source.title}
    </a>
  )
}
