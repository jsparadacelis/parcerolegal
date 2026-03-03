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
      <div className="flex items-center gap-2.5 bg-surface border-[1.5px] border-border hover:border-terra focus-within:border-terra focus-within:ring-2 focus-within:ring-terra-light rounded-xl px-4 py-3 transition-all duration-150">
        <svg className="text-terra w-4 h-4 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isLoading}
          placeholder="¿Me pueden despedir sin justa causa?"
          className="flex-1 bg-transparent text-sm text-ink placeholder:text-ink-3 font-normal outline-none disabled:cursor-not-allowed disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="bg-terra hover:bg-terra-mid active:bg-ink text-white text-xs font-bold px-3.5 py-2 rounded-lg transition-colors duration-150 whitespace-nowrap disabled:cursor-not-allowed disabled:opacity-50"
        >
          Preguntar
        </button>
      </div>
    </form>
  )
}
