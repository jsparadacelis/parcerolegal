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
      className="inline-flex items-center gap-1.5 text-xs font-semibold text-terra bg-terra-light border border-terra/12 px-3 py-1.5 rounded-lg hover:opacity-75 transition-opacity"
    >
      {source.title}
    </a>
  )
}
