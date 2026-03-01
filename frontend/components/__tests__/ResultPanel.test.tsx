import { render, screen } from '@testing-library/react'
import { ResultPanel } from '../ResultPanel'
import type { QueryResponse } from '@/lib/types'

describe('ResultPanel', () => {
  const mockResponse: QueryResponse = {
    answer: 'Según el **Artículo 15** de la Constitución...',
    sources: [
      {
        title: 'Constitución Política - Artículo 15',
        type: 'constitución',
        excerpt: 'Todas las personas tienen derecho a su intimidad personal...',
        similarity: 0.89,
      },
    ],
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
          title: 'Source 1',
          type: 'constitución',
          excerpt: 'Excerpt 1',
          similarity: 0.9,
        },
        {
          title: 'Source 2',
          type: 'sentencia',
          excerpt: 'Excerpt 2',
          similarity: 0.8,
        },
      ],
    }

    render(<ResultPanel response={multiSourceResponse} />)

    expect(screen.getByText('Source 1')).toBeInTheDocument()
    expect(screen.getByText('Source 2')).toBeInTheDocument()
  })

  it('shows out-of-scope message when no relevant sources', () => {
    const outOfScopeResponse: QueryResponse = {
      answer: 'Lo siento, tu pregunta está fuera del alcance...',
      sources: [],
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
    }

    render(<ResultPanel response={outOfScopeResponse} />)

    expect(screen.queryByText(/fuentes/i)).not.toBeInTheDocument()
  })
})
