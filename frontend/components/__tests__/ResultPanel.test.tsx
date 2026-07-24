import { render, screen } from '@testing-library/react'
import { ResultPanel } from '../ResultPanel'
import type { QueryResponse } from '@/lib/types'

describe('ResultPanel', () => {
  const mockResponse: QueryResponse = {
    answer: 'Según el **Artículo 15** de la Constitución...',
    sources: [
      {
        chunk_id: 'c1',
        source_type: 'constitucion',
        title: 'Constitución Política - Artículo 15',
        url: 'https://example.com/art15',
      },
    ],
    out_of_scope: false,
    processing_time_ms: 100,
  }

  it('renders the answer text', () => {
    const { container } = render(<ResultPanel response={mockResponse} />)

    expect(container.textContent).toMatch(/Según el.*Artículo 15.*de la Constitución/i)
  })

  it('renders markdown formatting in answer', () => {
    render(<ResultPanel response={mockResponse} />)

    const boldText = screen.getByText('Artículo 15')
    expect(boldText.tagName).toBe('STRONG')
  })

  it('displays sources section header', () => {
    render(<ResultPanel response={mockResponse} />)

    expect(screen.getByText(/fuentes/i)).toBeInTheDocument()
  })

  it('renders all source cards', () => {
    const multiSourceResponse: QueryResponse = {
      answer: 'Test answer',
      sources: [
        {
          chunk_id: 'c1',
          source_type: 'constitucion',
          title: 'Source 1',
          url: 'https://example.com/1',
        },
        {
          chunk_id: 'c2',
          source_type: 'sentencia',
          title: 'Source 2',
          url: 'https://example.com/2',
        },
      ],
      out_of_scope: false,
      processing_time_ms: 100,
    }

    render(<ResultPanel response={multiSourceResponse} />)

    expect(screen.getByText('Source 1')).toBeInTheDocument()
    expect(screen.getByText('Source 2')).toBeInTheDocument()
  })

  it('shows out-of-scope message when no relevant sources', () => {
    const outOfScopeResponse: QueryResponse = {
      answer: 'Lo siento, tu pregunta está fuera del alcance...',
      sources: [],
      out_of_scope: true,
      processing_time_ms: 50,
    }

    render(<ResultPanel response={outOfScopeResponse} />)

    expect(
      screen.getByText(/fuera del alcance/i)
    ).toBeInTheDocument()
  })

  it('does not render sources section when sources array is empty', () => {
    const outOfScopeResponse: QueryResponse = {
      answer: 'Out of scope',
      sources: [],
      out_of_scope: true,
      processing_time_ms: 50,
    }

    render(<ResultPanel response={outOfScopeResponse} />)

    expect(screen.queryByText(/fuentes/i)).not.toBeInTheDocument()
  })

  it('renders the copy and share actions', () => {
    render(<ResultPanel response={mockResponse} query="¿Qué es el habeas corpus?" />)

    expect(screen.getByRole('button', { name: /copiar texto/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /compartir/i })).toBeInTheDocument()
  })
})
