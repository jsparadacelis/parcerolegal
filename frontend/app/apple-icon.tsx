import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const size = { width: 180, height: 180 }
export const contentType = 'image/png'

// Monograma "p" + punto de acento (reemplaza la casita).
export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          background: '#14161C',
          width: '100%',
          height: '100%',
          borderRadius: 40,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          fontFamily: 'sans-serif',
          fontWeight: 800,
          fontSize: 118,
          color: '#FFFFFF',
        }}
      >
        p
        <div
          style={{
            position: 'absolute',
            top: 38,
            right: 38,
            width: 26,
            height: 26,
            borderRadius: 26,
            background: '#2457D6',
          }}
        />
      </div>
    ),
    { ...size },
  )
}
