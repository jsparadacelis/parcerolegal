import { render, screen } from '@testing-library/react'
import { SourceCard } from '../SourceCard'
import type { Source } from '@/lib/types'

describe('SourceCard', () => {
  const mockSource: Source = {
    chunk_id: 'c1',
    source_type: 'constitucion',
    title: 'Constitución Política - Artículo 15',
    url: 'https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=4125#15',
  }

  it('displays source title', () => {
    render(<SourceCard source={mockSource} />)

    expect(screen.getByText('Constitución Política - Artículo 15')).toBeInTheDocument()
  })

  it('links to the source url', () => {
    render(<SourceCard source={mockSource} />)

    expect(screen.getByRole('link')).toHaveAttribute('href', mockSource.url)
  })

  it('opens the link in a new tab safely', () => {
    render(<SourceCard source={mockSource} />)

    const link = screen.getByRole('link')
    expect(link).toHaveAttribute('target', '_blank')
    expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('renders for sentencia sources too', () => {
    const sentenciaSource: Source = { ...mockSource, source_type: 'sentencia', title: 'T-760-08' }
    render(<SourceCard source={sentenciaSource} />)

    expect(screen.getByText('T-760-08')).toBeInTheDocument()
  })
})
