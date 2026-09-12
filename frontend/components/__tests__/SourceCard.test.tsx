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

  // Cada corpus debe anunciarse por su nombre: atribuir un artículo del Código
  // Penal a la Corte Constitucional es una cita falsa.
  it.each([
    ['constitucion', 'Constitución Política'],
    ['sentencia', 'Corte Constitucional'],
    ['codigo_penal', 'Código Penal'],
    ['codigo_sustantivo_trabajo', 'Código Sustantivo del Trabajo'],
  ] as const)('labels a %s source as "%s"', (sourceType, label) => {
    render(<SourceCard source={{ ...mockSource, source_type: sourceType }} />)

    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it('falls back to a generic label for an unknown source type', () => {
    const unknownSource = { ...mockSource, source_type: 'codigo_civil' } as unknown as Source
    render(<SourceCard source={unknownSource} />)

    expect(screen.getByText('Fuente legal')).toBeInTheDocument()
    expect(screen.queryByText('Corte Constitucional')).not.toBeInTheDocument()
    expect(screen.getByRole('link')).toHaveAttribute('href', mockSource.url)
  })
})
