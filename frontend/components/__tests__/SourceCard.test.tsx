import { render, screen } from '@testing-library/react'
import { SourceCard } from '../SourceCard'

describe('SourceCard', () => {
  const mockSource = {
    title: 'Constitución Política - Artículo 15',
    type: 'constitución' as const,
    excerpt: 'Todas las personas tienen derecho a su intimidad personal...',
    similarity: 0.89,
  }

  it('displays source title', () => {
    render(<SourceCard source={mockSource} />)

    expect(screen.getByText('Constitución Política - Artículo 15')).toBeInTheDocument()
  })

  it('shows excerpt preview', () => {
    render(<SourceCard source={mockSource} />)

    expect(
      screen.getByText(/Todas las personas tienen derecho/i)
    ).toBeInTheDocument()
  })

  it('displays similarity score as percentage', () => {
    render(<SourceCard source={mockSource} />)

    expect(screen.getByText('89%')).toBeInTheDocument()
  })

  it('applies constitution styling for constitution type', () => {
    const { container } = render(<SourceCard source={mockSource} />)

    expect(container.querySelector('.border-sky-500\\/30')).toBeInTheDocument()
  })

  it('applies sentencia styling for sentencia type', () => {
    const sentenciaSource = { ...mockSource, type: 'sentencia' as const }
    const { container } = render(<SourceCard source={sentenciaSource} />)

    expect(container.querySelector('.border-purple-500\\/30')).toBeInTheDocument()
  })

  it('truncates long excerpts with ellipsis', () => {
    const longSource = {
      ...mockSource,
      excerpt: 'A'.repeat(200),
    }
    const { container } = render(<SourceCard source={longSource} />)

    const excerptElement = container.querySelector('[data-testid="source-excerpt"]')
    expect(excerptElement).toHaveClass('line-clamp-3')
  })
})
