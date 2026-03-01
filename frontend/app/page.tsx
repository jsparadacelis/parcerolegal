'use client'

import { useState } from 'react'
import { SearchBox } from '@/components/SearchBox'
import { LoadingSkeleton } from '@/components/LoadingSkeleton'
import { ResultPanel } from '@/components/ResultPanel'
import { Disclaimer } from '@/components/Disclaimer'
import { simulateQuery, EXAMPLE_QUERY } from '@/lib/mockData'
import type { QueryResponse } from '@/lib/types'

export default function Home() {
  const [isLoading, setIsLoading] = useState(false)
  const [response, setResponse] = useState<QueryResponse | null>(null)

  const handleSubmit = async (query: string) => {
    setIsLoading(true)
    setResponse(null)

    const result = await simulateQuery(query)

    setResponse(result)
    setIsLoading(false)
  }

  const handleExampleClick = () => {
    handleSubmit(EXAMPLE_QUERY)
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-800/50">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-yellow-500">
            parcero<span className="text-slate-300">legal</span>.co
          </h1>
        </div>
      </header>

      {/* Main */}
      <main className="container mx-auto max-w-4xl px-4 py-12">
        {/* Hero */}
        {!response && !isLoading && (
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-4xl font-bold tracking-tight text-slate-100">
              Busca en la legislación colombiana
            </h2>
            <p className="mb-8 text-lg text-slate-400">
              Motor de búsqueda legal gratuito con IA. Encuentra respuestas basadas en
              la Constitución y jurisprudencia de Colombia.
            </p>
          </div>
        )}

        {/* Search Box */}
        <SearchBox onSubmit={handleSubmit} isLoading={isLoading} />

        {/* Example */}
        {!response && !isLoading && (
          <div className="mt-6 text-center">
            <button
              onClick={handleExampleClick}
              className="text-sm text-slate-400 underline-offset-2 hover:text-yellow-500 hover:underline"
            >
              Prueba: &quot;{EXAMPLE_QUERY}&quot;
            </button>
          </div>
        )}

        {/* Loading */}
        {isLoading && <LoadingSkeleton />}

        {/* Results */}
        {response && (
          <>
            <ResultPanel response={response} />
            <Disclaimer />
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-slate-700 py-8">
        <div className="container mx-auto px-4 text-center text-sm text-slate-500">
          <p>
            Beta · Los resultados se basan en IA y pueden contener errores ·{' '}
            <a href="#" className="text-sky-400 hover:underline">
              Acerca de
            </a>
          </p>
        </div>
      </footer>
    </div>
  )
}
