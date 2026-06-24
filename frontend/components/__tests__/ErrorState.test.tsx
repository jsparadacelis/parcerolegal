import { render, screen } from '@testing-library/react'
import { ErrorState } from '../ErrorState'

describe('ErrorState', () => {
  it('renders the given message', () => {
    render(<ErrorState message="No pudimos conectar con el servidor." />)

    expect(screen.getByText('No pudimos conectar con el servidor.')).toBeInTheDocument()
  })
})
