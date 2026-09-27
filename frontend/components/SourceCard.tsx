import type { Source, SourceType } from '@/lib/types'

interface SourceCardProps {
  source: Source
}

interface SourceMeta {
  /** Texto del ícono: el glifo de la Constitución o la sigla del código/corpus. */
  badge: string
  /** Clases del cuadro del ícono (fondo + tinta). */
  chipClass: string
  /** Clases del badge: la sigla va en mono, el § en display. */
  badgeClass: string
  /** Subtítulo de la tarjeta: de dónde sale la fuente. */
  label: string
}

// El oro queda reservado para la jurisprudencia (acento, según el design system)
// y el azul para la Constitución; los códigos usan la tinta neutra y se
// distinguen por la sigla, que es lo que un lector reconoce de un vistazo.
const SOURCE_META: Record<SourceType, SourceMeta> = {
  constitucion: {
    badge: '§',
    chipClass: 'bg-primary-tint text-primary',
    badgeClass: 'font-display font-bold text-[14px] leading-none',
    label: 'Constitución Política',
  },
  sentencia: {
    badge: 'C',
    chipClass: 'bg-gold-tint text-gold-ink',
    badgeClass: 'font-mono font-bold text-[11px] leading-none',
    label: 'Corte Constitucional',
  },
  codigo_penal: {
    badge: 'CP',
    chipClass: 'bg-surface-3 text-ink-2',
    badgeClass: 'font-mono font-bold text-[11px] leading-none',
    label: 'Código Penal',
  },
  codigo_sustantivo_trabajo: {
    badge: 'CST',
    chipClass: 'bg-surface-3 text-ink-2',
    badgeClass: 'font-mono font-bold text-[9px] leading-none',
    label: 'Código Sustantivo del Trabajo',
  },
  codigo_civil: {
    badge: 'CC',
    chipClass: 'bg-surface-3 text-ink-2',
    badgeClass: 'font-mono font-bold text-[11px] leading-none',
    label: 'Código Civil',
  },
}

// Si el backend suma un corpus que el frontend todavía no conoce, la tarjeta se
// degrada a algo genérico y cierto. Nunca debe heredar la etiqueta de otro
// corpus: una fuente mal atribuida rompe la promesa de fuentes verificables.
const FALLBACK_META: SourceMeta = {
  badge: '§',
  chipClass: 'bg-surface-3 text-ink-2',
  badgeClass: 'font-display font-bold text-[14px] leading-none',
  label: 'Fuente legal',
}

export function SourceCard({ source }: SourceCardProps) {
  const meta = SOURCE_META[source.source_type] ?? FALLBACK_META

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
          meta.chipClass
        }
      >
        <span className={meta.badgeClass}>{meta.badge}</span>
      </span>

      {/* Título + subtítulo */}
      <span className="flex-1 min-w-0">
        <span className="block text-[13.5px] font-semibold text-ink truncate">
          {source.title}
        </span>
        <span className="block text-[11.5px] text-ink-3 truncate">{meta.label}</span>
      </span>

      {/* Flecha: señal de clicable */}
      <span className="flex-none text-primary text-[16px] font-bold transition-transform group-hover:translate-x-0.5">
        →
      </span>
    </a>
  )
}
