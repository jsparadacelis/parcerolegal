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
          background: '#F5F8FE',
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
        {/* Monograma */}
        <div
          style={{
            width: 96,
            height: 96,
            background: '#14161C',
            borderRadius: 24,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            marginBottom: 36,
            fontSize: 62,
            fontWeight: 800,
            color: '#FFFFFF',
          }}
        >
          p
          <div
            style={{
              position: 'absolute',
              top: 20,
              right: 20,
              width: 14,
              height: 14,
              borderRadius: 14,
              background: '#2457D6',
            }}
          />
        </div>

        {/* Wordmark */}
        <div style={{ display: 'flex', marginBottom: 20 }}>
          <span style={{ fontSize: 80, fontWeight: 800, color: '#14161C', letterSpacing: '-3px' }}>
            parcero
          </span>
          <span style={{ fontSize: 80, fontWeight: 800, color: '#2457D6', letterSpacing: '-3px' }}>
            legal
          </span>
        </div>

        {/* Tagline */}
        <div style={{ fontSize: 36, fontWeight: 500, color: '#3A3F49', marginBottom: 48 }}>
          tu derecho, claro.
        </div>

        {/* Description */}
        <div
          style={{
            fontSize: 24,
            color: '#6A7180',
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
