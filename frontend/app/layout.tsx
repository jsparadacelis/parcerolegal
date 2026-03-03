import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "parcerolegal — tu derecho, claro",
  description: "Motor de búsqueda legal gratuito para Colombia. Encuentra respuestas basadas en la Constitución y jurisprudencia.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
