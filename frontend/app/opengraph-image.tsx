import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const alt = 'parcerolegal — tu derecho, claro'
export const size = { width: 1200, height: 630 }
export const contentType = 'image/png'

export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          background: '#FFF7F3',
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '80px',
          fontFamily: 'system-ui, sans-serif',
        }}
      >
        {/* Logo mark */}
        <div
          style={{
            width: 80,
            height: 80,
            background: '#C2410C',
            borderRadius: 20,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: 36,
          }}
        >
          <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3L4 9v12h16V9L12 3z" />
            <path d="M9 15l3 3 3-3" />
            <path d="M12 18V9" />
          </svg>
        </div>

        {/* Wordmark */}
        <div style={{ display: 'flex', marginBottom: 20 }}>
          <span style={{ fontSize: 80, fontWeight: 700, color: '#1C1412', letterSpacing: '-3px' }}>
            parcero
          </span>
          <span style={{ fontSize: 80, fontWeight: 400, color: '#A08070', letterSpacing: '-3px' }}>
            legal
          </span>
        </div>

        {/* Tagline */}
        <div style={{ fontSize: 36, fontWeight: 400, color: '#5C4033', marginBottom: 48 }}>
          tu derecho, claro.
        </div>

        {/* Description */}
        <div
          style={{
            fontSize: 24,
            color: '#A08070',
            textAlign: 'center',
            maxWidth: 820,
            lineHeight: 1.5,
          }}
        >
          Constitución Política + jurisprudencia colombiana — gratis, en lenguaje normal.
        </div>
      </div>
    ),
    { ...size },
  )
}
