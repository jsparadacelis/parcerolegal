import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL('https://parcerolegal.co'),
  title: "parcerolegal — tu derecho, claro",
  description: "Buscador legal gratis para Colombia: Constitución, sentencias de la Corte Constitucional, Código Penal, Código Sustantivo del Trabajo y Código Civil.",
  alternates: {
    canonical: '/',
  },
  openGraph: {
    type: 'website',
    locale: 'es_CO',
    url: 'https://parcerolegal.co',
    siteName: 'parcerolegal',
    title: 'parcerolegal — tu derecho, claro',
    description: 'Buscador legal gratis para Colombia: Constitución, sentencias de la Corte Constitucional, Código Penal, Código Sustantivo del Trabajo y Código Civil.',
    images: [{ url: '/opengraph-image', width: 1200, height: 630, alt: 'parcerolegal — tu derecho, claro' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'parcerolegal — tu derecho, claro',
    description: 'Buscador legal gratis para Colombia: Constitución, sentencias de la Corte Constitucional, Código Penal, Código Sustantivo del Trabajo y Código Civil.',
    images: ['/opengraph-image'],
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <head>
        {/* Cielo Andino: Bricolage Grotesque (display) + Instrument Sans (cuerpo) + Space Mono (mono) */}
        <link
          href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700;12..96,800&family=Instrument+Sans:ital,wght@0,400;0,500;0,600;1,400&family=Space+Mono:wght@400;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
