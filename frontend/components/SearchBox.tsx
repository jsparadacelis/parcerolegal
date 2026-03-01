'use client'

import { useState, FormEvent } from 'react'

interface SearchBoxProps {
  onSubmit: (query: string) => void
  isLoading?: boolean
}

export function SearchBox({ onSubmit, isLoading = false }: SearchBoxProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (query.trim()) {
      onSubmit(query)
      setQuery('')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isLoading}
          placeholder="Haz tu pregunta sobre legislación colombiana..."
          className="flex-1 rounded-lg border border-slate-600 bg-slate-800 px-4 py-3 text-slate-100 placeholder-slate-500 transition-colors focus:border-yellow-500 focus:outline-none focus:ring-2 focus:ring-yellow-500/20 disabled:cursor-not-allowed disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="rounded-lg bg-yellow-500 px-6 py-3 font-semibold text-slate-900 transition-colors hover:bg-yellow-400 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Preguntar
        </button>
      </div>
    </form>
  )
}
