'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { SearchBox } from '@/components/SearchBox'
import { LoadingSkeleton } from '@/components/LoadingSkeleton'
import { ResultPanel } from '@/components/ResultPanel'
import { ErrorState } from '@/components/ErrorState'
import { Logo } from '@/components/Logo'
import { queryLegal, getShare, ApiError } from '@/lib/api'
import type { QueryResponse } from '@/lib/types'

const EXAMPLE_QUERY = '¿Qué es el habeas corpus y cómo lo puedo usar?'

export default function SharedQueryPage() {
  const params = useParams<{ id: string }>()
  const shareId = params.id

  const [isLoading, setIsLoading] = useState(false)
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  // Guardamos la pregunta enviada para mostrarla como burbuja del usuario.
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [initialValue, setInitialValue] = useState('')

  const handleSubmit = async (query: string) => {
    setIsLoading(true)
    setResponse(null)
    setError(null)
    setSubmittedQuery(query)

    try {
      const result = await queryLegal(query)
      setResponse(result)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Algo salió mal. Intenta de nuevo.')
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (!shareId) return
    let cancelled = false

    getShare(shareId).then((shared) => {
      if (cancelled || !shared) return
      setInitialValue(shared.question)
      handleSubmit(shared.question)
    })

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shareId])

  const handleExampleClick = () => handleSubmit(EXAMPLE_QUERY)

  return (
    <div className="min-h-screen bg-surface-2">
      {/* Navbar */}
      <nav className="flex items-center px-5 py-3.5 border-b border-border bg-surface">
        <a
          href="/"
          className="flex items-center cursor-pointer rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
          aria-label="Volver al inicio"
        >
          <Logo size={19} />
        </a>
      </nav>

      {/* Main */}
      <main className="container mx-auto max-w-3xl px-4 py-8 sm:py-12">
        {/* Hero */}
        {!response && !isLoading && !error && (
          <div className="mb-8 sm:mb-10 text-center">
            <h1 className="font-display mb-3 text-3xl sm:text-4xl font-extrabold tracking-tight text-ink">
              Tu derecho, claro.
            </h1>
            <p className="mb-6 sm:mb-8 text-base sm:text-lg text-ink-2 font-normal">
              Consulta la Constitución y jurisprudencia colombiana en lenguaje normal.
              Gratis, sin traje, sin protocolo.
            </p>
          </div>
        )}

        {/* Search Box */}
        <SearchBox onSubmit={handleSubmit} isLoading={isLoading} initialValue={initialValue} />

        {/* Disclaimer hint — debajo del buscador */}
        <div className="mt-3 flex items-center justify-center gap-1.5">
          <svg
            className="w-[13px] h-[13px] flex-none text-ink-3/70"
            viewBox="0 0 24 24" fill="none" stroke="currentColor"
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
          <span className="text-[12px] text-ink-3/70">
            Orientativo · no reemplaza a un abogado
          </span>
        </div>

        {/* Example */}
        {!response && !isLoading && !error && (
          <div className="mt-5 text-center">
            <button
              onClick={handleExampleClick}
              className="text-sm text-ink-3 hover:text-primary transition-colors duration-150 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
            >
              Prueba: &quot;{EXAMPLE_QUERY}&quot;
            </button>
          </div>
        )}

        {/* Loading */}
        {isLoading && <LoadingSkeleton />}

        {/* Error */}
        {error && !isLoading && <ErrorState message={error} />}

        {/* Results */}
        {response && <ResultPanel response={response} query={submittedQuery} />}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-border py-8">
        <div className="container mx-auto px-4 text-center text-sm text-ink-3">
          <p>
            Beta · Los resultados se basan en IA y pueden contener errores ·{' '}
            <a href="/about" className="text-primary hover:underline underline-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:rounded">
              Acerca de
            </a>
            {' '}·{' '}
            <a
              href="https://github.com/jsparadacelis/parcerolegal/issues"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline underline-offset-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:rounded"
            >
              Reportar error
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}
