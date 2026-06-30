import { ImageResponse } from 'next/og'

export const runtime = 'edge'
export const size = { width: 32, height: 32 }
export const contentType = 'image/png'

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          background: '#C2410C',
          width: '100%',
          height: '100%',
          borderRadius: 7,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 3L4 9v12h16V9L12 3z" />
          <path d="M9 15l3 3 3-3" />
          <path d="M12 18V9" />
        </svg>
      </div>
    ),
    { ...size },
  )
}
