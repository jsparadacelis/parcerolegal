import { render, screen } from '@testing-library/react'
import { LoadingSkeleton } from '../LoadingSkeleton'

describe('LoadingSkeleton', () => {
  it('displays loading message for users', () => {
    render(<LoadingSkeleton />)

    expect(
      screen.getByText(/analizando.*legislación/i)
    ).toBeInTheDocument()
  })

  it('shows animated skeleton for answer section', () => {
    const { container } = render(<LoadingSkeleton />)

    const skeletons = container.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('displays placeholder for source cards', () => {
    const { container } = render(<LoadingSkeleton />)

    const sourceSkeletons = container.querySelectorAll('[data-testid="source-skeleton"]')
    expect(sourceSkeletons).toHaveLength(3)
  })

  it('has appropriate ARIA attributes for accessibility', () => {
    const { container } = render(<LoadingSkeleton />)

    expect(container.querySelector('[aria-busy="true"]')).toBeInTheDocument()
    expect(container.querySelector('[aria-live="polite"]')).toBeInTheDocument()
  })
})
