'use client'

import { useState } from 'react'
import { SearchBox } from '@/components/SearchBox'
import { LoadingSkeleton } from '@/components/LoadingSkeleton'
import { ResultPanel } from '@/components/ResultPanel'
import { ErrorState } from '@/components/ErrorState'
import { queryLegal, ApiError } from '@/lib/api'
import type { QueryResponse } from '@/lib/types'

const EXAMPLE_QUERY = '¿Puedo grabar una llamada sin permiso de la otra persona?'

export default function Home() {
  const [isLoading, setIsLoading] = useState(false)
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (query: string) => {
    setIsLoading(true)
    setResponse(null)
    setError(null)

    try {
      const result = await queryLegal(query)
      setResponse(result)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Algo salió mal. Intenta de nuevo.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleExampleClick = () => {
    handleSubmit(EXAMPLE_QUERY)
  }

  const handleReset = () => {
    setResponse(null)
    setError(null)
    setIsLoading(false)
  }

  return (
    <div className="min-h-screen bg-surface-2">
      {/* Navbar */}
      <nav className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface">
        <button onClick={handleReset} className="flex items-center gap-2.5 cursor-pointer">
          <div className="w-7 h-7 bg-terra rounded-[7px] flex items-center justify-center flex-shrink-0">
            <svg className="text-white w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 3L4 9v12h16V9L12 3z" />
              <path d="M9 15l3 3 3-3" />
              <path d="M12 18V9" />
            </svg>
          </div>
          <span className="text-base font-bold tracking-tight text-ink">
            parcero<span className="font-normal text-ink-3">legal</span>
          </span>
        </button>
        <span className="text-[11px] font-medium text-ink-3 bg-surface-2 border border-border px-2.5 py-1 rounded-full">
          No reemplaza un abogado
        </span>
      </nav>

      {/* Main */}
      <main className="container mx-auto max-w-3xl px-4 py-12">
        {/* Hero */}
        {!response && !isLoading && !error && (
          <div className="mb-10 text-center">
            <h1 className="mb-3 text-4xl font-bold tracking-tight text-ink">
              tu derecho, claro.
            </h1>
            <p className="mb-8 text-lg text-ink-2 font-normal">
              Consultá la Constitución y jurisprudencia colombiana en lenguaje normal.
              Gratis, sin traje, sin protocolo.
            </p>
          </div>
        )}

        {/* Search Box */}
        <SearchBox onSubmit={handleSubmit} isLoading={isLoading} />

        {/* Example */}
        {!response && !isLoading && !error && (
          <div className="mt-5 text-center">
            <button
              onClick={handleExampleClick}
              className="text-sm text-ink-3 hover:text-terra transition-colors duration-150"
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
        {response && <ResultPanel response={response} />}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-border py-8">
        <div className="container mx-auto px-4 text-center text-sm text-ink-3">
          <p>
            Beta · Los resultados se basan en IA y pueden contener errores ·{' '}
            <a href="#" className="text-terra hover:underline underline-offset-2">
              Acerca de
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}
