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
      <div className="flex items-center gap-3 bg-surface border-[1.5px] border-border hover:border-primary focus-within:border-primary focus-within:shadow-[0_0_0_3px_var(--color-primary-tint)] rounded-[12px] px-4 py-3 transition-all duration-150 min-h-[52px]">
        <svg className="text-primary w-[18px] h-[18px] flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isLoading}
          placeholder="¿Me pueden despedir sin justa causa?"
          className="flex-1 bg-transparent text-base text-ink placeholder:text-ink-3 font-normal outline-none disabled:cursor-not-allowed disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading}
          className="bg-primary hover:bg-primary-hover active:bg-ink text-white text-[13px] font-bold px-4 py-2 min-h-[44px] rounded-[8px] transition-colors duration-150 whitespace-nowrap disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
        >
          Preguntar
        </button>
      </div>
    </form>
  )
}
