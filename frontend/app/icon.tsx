import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const size = { width: 32, height: 32 }
export const contentType = 'image/png'

// Monograma "p" + punto de acento (reemplaza la casita).
export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          background: '#14161C',
          width: '100%',
          height: '100%',
          borderRadius: 8,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
          fontFamily: 'sans-serif',
          fontWeight: 800,
          fontSize: 22,
          color: '#FFFFFF',
        }}
      >
        p
        <div
          style={{
            position: 'absolute',
            top: 7,
            right: 7,
            width: 5,
            height: 5,
            borderRadius: 5,
            background: '#2457D6',
          }}
        />
      </div>
    ),
    { ...size },
  )
}
