// Wordmark "parcerolegal" + destello (reemplaza el ícono de casita).
// El destello: cruz (+) en primary + chispa diagonal en gold.

interface LogoProps {
  /** Tamaño de fuente del wordmark en px. Default 19 (navbar). */
  size?: number
  /** Variante sobre fondo oscuro. */
  onDark?: boolean
}

export function Logo({ size = 19, onDark = false }: LogoProps) {
  const s = size / 19 // factor de escala relativo al default
  const legalColor = onDark ? '#7FA0F0' : 'var(--color-primary)'
  const textColor = onDark ? '#FFFFFF' : 'var(--color-ink)'

  // Geometría del destello, proporcional al tamaño de fuente.
  const box = Math.round(size * 0.58)
  const bar = Math.max(1.8, size * 0.15)
  const barColor = onDark ? '#7FA0F0' : 'var(--color-primary)'

  return (
    <span style={{ display: 'inline-flex', alignItems: 'flex-start', gap: 4 * s }}>
      <span
        className="font-display"
        style={{
          fontWeight: 800,
          fontSize: size,
          lineHeight: 1,
          letterSpacing: '-0.03em',
          color: textColor,
        }}
      >
        parcero<span style={{ color: legalColor }}>legal</span>
      </span>

      {/* Destello */}
      <span style={{ position: 'relative', width: box, height: box, marginTop: size * 0.06 }}>
        <span style={{ position: 'absolute', top: (box - bar) / 2, left: 0, width: box, height: bar, borderRadius: bar, background: barColor }} />
        <span style={{ position: 'absolute', top: 0, left: (box - bar) / 2, width: bar, height: box, borderRadius: bar, background: barColor }} />
        <span style={{ position: 'absolute', top: box * 0.14, left: box * 0.72, width: bar * 0.85, height: box * 0.38, borderRadius: bar, background: 'var(--color-gold)', transform: 'rotate(45deg)' }} />
      </span>
    </span>
  )
}
