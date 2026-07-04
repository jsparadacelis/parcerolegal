import type { Source } from '@/lib/types'

interface SourceCardProps {
  source: Source
}

export function SourceCard({ source }: SourceCardProps) {
  const isConst = source.source_type === 'constitucion'

  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex items-center gap-3 bg-surface border border-primary-border rounded-[10px] px-[13px] py-[11px] hover:border-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-1"
    >
      {/* Ícono según tipo de fuente */}
      <span
        className={
          'flex-none w-[30px] h-[30px] rounded-[8px] flex items-center justify-center ' +
          (isConst ? 'bg-primary-tint text-primary' : 'bg-gold-tint text-gold-ink')
        }
      >
        {isConst ? (
          <span className="font-display font-bold text-[14px] leading-none">§</span>
        ) : (
          <span className="font-mono font-bold text-[11px] leading-none">C</span>
        )}
      </span>

      {/* Título + subtítulo */}
      <span className="flex-1 min-w-0">
        <span className="block text-[13.5px] font-semibold text-ink truncate">
          {source.title}
        </span>
        <span className="block text-[11.5px] text-ink-3 truncate">
          {isConst ? 'Constitución Política' : 'Corte Constitucional'}
        </span>
      </span>

      {/* Flecha: señal de clicable */}
      <span className="flex-none text-primary text-[16px] font-bold transition-transform group-hover:translate-x-0.5">
        →
      </span>
    </a>
  )
}
