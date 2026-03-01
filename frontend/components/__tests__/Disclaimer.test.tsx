import { render, screen } from '@testing-library/react'
import { Disclaimer } from '../Disclaimer'

describe('Disclaimer', () => {
  it('displays beta warning message', () => {
    render(<Disclaimer />)

    expect(screen.getByText(/beta/i)).toBeInTheDocument()
  })

  it('warns users about information accuracy', () => {
    render(<Disclaimer />)

    expect(
      screen.getByText(/no constituye asesoría legal/i)
    ).toBeInTheDocument()
  })

  it('recommends consulting professionals', () => {
    render(<Disclaimer />)

    expect(
      screen.getByText(/consulta.*profesional/i)
    ).toBeInTheDocument()
  })

  it('has warning visual styling', () => {
    const { container } = render(<Disclaimer />)
    const disclaimer = container.firstChild

    expect(disclaimer).toHaveClass('border-yellow-500/20')
  })
})
