import Link from 'next/link'
import type { Metadata } from 'next'
import { Logo } from '@/components/Logo'

export const metadata: Metadata = {
  title: 'Acerca de — parcerolegal',
  description: 'Qué es parcerolegal, de dónde vienen las respuestas y cuáles son sus limitaciones.',
}

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-surface-2">
      {/* Navbar */}
      <nav className="flex items-center px-5 py-3.5 border-b border-border bg-surface">
        <Link href="/" className="flex items-center rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2" aria-label="Volver al inicio">
          <Logo size={19} />
        </Link>
      </nav>

      {/* Content */}
      <main className="container mx-auto max-w-2xl px-4 py-10 sm:py-14">
        <h1 className="font-display mb-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-ink">
          Acerca de parcerolegal
        </h1>
        <p className="mb-10 text-base text-ink-3">
          El amigo que estudió derecho. Gratis, sin traje, sin protocolo.
        </p>

        {/* Qué es */}
        <section className="mb-8">
          <h2 className="mb-3 text-base font-semibold text-ink">¿Qué es esto?</h2>
          <p className="text-sm leading-relaxed text-ink-2">
            parcerolegal es un motor de búsqueda legal gratuito para Colombia. Le puedes hacer
            preguntas en lenguaje normal — sin jerga, sin formalismos — y te responde con
            información real de la Constitución Política y sentencias de la Corte Constitucional.
            No hay trampa: cada respuesta incluye las fuentes donde fue tomada.
          </p>
        </section>

        {/* Fuentes */}
        <section className="mb-8">
          <h2 className="mb-3 text-base font-semibold text-ink">¿De dónde vienen las respuestas?</h2>
          <p className="mb-3 text-sm leading-relaxed text-ink-2">
            Las respuestas se construyen a partir de dos fuentes oficiales:
          </p>
          <ul className="mb-3 space-y-2 text-sm text-ink-2">
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-primary font-semibold flex-shrink-0">—</span>
              <span>
                <strong className="text-ink font-semibold">Constitución Política de Colombia (1991)</strong>
                {' '}— los 380 artículos completos.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <span className="mt-0.5 text-primary font-semibold flex-shrink-0">—</span>
              <span>
                <strong className="text-ink font-semibold">25 sentencias de la Corte Constitucional</strong>
                {' '}— entre ellas T-760/2008 (salud), C-355/2006 (aborto), SU-214/2016
                (matrimonio igualitario), T-025/2004 (desplazamiento), T-881/2002 (dignidad humana),
                C-024/1994 (libertad personal), T-622/2016 (Río Atrato), y otras hito en
                derechos fundamentales colombianos.
              </span>
            </li>
          </ul>
          <p className="text-sm leading-relaxed text-ink-2">
            Todos los textos provienen directamente de{' '}
            <a
              href="https://www.corteconstitucional.gov.co"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline underline-offset-2 hover:opacity-75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:rounded"
            >
              corteconstitucional.gov.co
            </a>
            .
          </p>
        </section>

        {/* Cómo funciona */}
        <section className="mb-8">
          <h2 className="mb-3 text-base font-semibold text-ink">¿Cómo funciona?</h2>
          <p className="text-sm leading-relaxed text-ink-2">
            Cuando haces una pregunta, el sistema busca los fragmentos más relevantes
            del corpus legal usando búsqueda semántica (no por palabras clave exactas).
            Con esos fragmentos como contexto, un modelo de lenguaje genera una respuesta
            en español claro. Si no encuentra nada suficientemente relevante, lo dice
            directamente en lugar de inventar.
          </p>
        </section>

        {/* Limitaciones / disclaimer */}
        <section className="mb-8">
          <h2 className="mb-3 text-base font-semibold text-ink">Limitaciones importantes</h2>
          <div className="rounded-xl border border-border bg-surface px-5 py-5 shadow-sm">
            <div className="mb-3.5 flex items-center gap-2 border-b border-surface-3 pb-3.5">
              <span className="text-warn text-[13px] leading-none" aria-hidden="true">⚠</span>
              <span className="font-mono text-[10.5px] font-bold uppercase tracking-[0.12em] text-warn">
                Lee esto antes
              </span>
            </div>
            <p className="mb-3 text-[14.5px] leading-relaxed text-ink-2">
              <strong className="text-ink font-semibold">parcerolegal no es asesoría jurídica</strong>
              {' '}y no reemplaza a un abogado. Las respuestas son orientativas — pueden
              contener errores, estar desactualizadas o no aplicar a tu situación específica.
            </p>
            <p className="mb-3 text-[14.5px] leading-relaxed text-ink-2">
              El corpus cubre principalmente la Constitución del 91 y jurisprudencia
              constitucional seleccionada. Temas de derecho civil, penal, laboral, comercial
              o administrativo pueden no estar cubiertos o cubiertos parcialmente.
            </p>
            <p className="text-[14.5px] leading-relaxed text-ink-2">
              Para decisiones legales que te afecten — una tutela, un contrato, un proceso
              judicial — consulta siempre con un abogado. En Colombia puedes acceder a{' '}
              <strong className="text-ink font-semibold">consultorios jurídicos gratuitos</strong>
              {' '}en universidades y en la Defensoría del Pueblo.
            </p>
          </div>
        </section>

        {/* Proyecto / contacto */}
        <section className="mb-10">
          <h2 className="mb-3 text-base font-semibold text-ink">El proyecto</h2>
          <p className="text-sm leading-relaxed text-ink-2">
            parcerolegal es un proyecto independiente, sin ánimo de lucro, construido con
            la convicción de que el acceso a la información legal no debería ser exclusivo
            de quienes pueden pagar un abogado. Está en beta — si encuentras errores o tienes
            sugerencias, los puedes reportar en{' '}
            <a
              href="https://github.com/jsparadacelis/parcerolegal/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline underline-offset-2 hover:opacity-75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:rounded"
            >
              GitHub
            </a>
            .
          </p>
        </section>

        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:opacity-75 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 rounded"
        >
          <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z" clipRule="evenodd" />
          </svg>
          Volver a preguntar
        </Link>
      </main>

      {/* Footer */}
      <footer className="mt-8 border-t border-border py-8">
        <div className="container mx-auto px-4 text-center text-sm text-ink-3">
          <p>Beta · parcerolegal.co</p>
        </div>
      </footer>
    </div>
  )
}
