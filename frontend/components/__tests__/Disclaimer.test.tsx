import { render, screen } from '@testing-library/react'
import { Disclaimer } from '../Disclaimer'

describe('Disclaimer', () => {
  it('displays warning icon', () => {
    render(<Disclaimer />)

    expect(screen.getByText(/orientativa/i)).toBeInTheDocument()
  })

  it('warns users about information accuracy', () => {
    render(<Disclaimer />)

    expect(
      screen.getByText(/no reemplaza.*asesoría/i)
    ).toBeInTheDocument()
  })

  it('recommends consulting professionals', () => {
    render(<Disclaimer />)

    expect(
      screen.getByText(/profesional para tu caso/i)
    ).toBeInTheDocument()
  })

  it('has amber warning visual styling', () => {
    const { container } = render(<Disclaimer />)
    const disclaimer = container.firstChild

    expect(disclaimer).toHaveClass('border-amber')
  })
})
