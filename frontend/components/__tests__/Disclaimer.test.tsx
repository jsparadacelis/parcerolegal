import { render, screen } from '@testing-library/react'
import { Disclaimer } from '../Disclaimer'

describe('Disclaimer', () => {
  it('displays the orientative notice', () => {
    render(<Disclaimer />)

    expect(screen.getByText(/orientativo/i)).toBeInTheDocument()
  })

  it('warns that it does not replace a lawyer', () => {
    render(<Disclaimer />)

    expect(
      screen.getByText(/no reemplaza a un abogado/i)
    ).toBeInTheDocument()
  })

  it('recommends consulting professionals', () => {
    render(<Disclaimer />)

    expect(
      screen.getByText(/consulta a un profesional/i)
    ).toBeInTheDocument()
  })

  it('is styled as an integrated fine-print footer', () => {
    const { container } = render(<Disclaimer />)
    const disclaimer = container.firstChild

    expect(disclaimer).toHaveClass('border-t')
    expect(disclaimer).toHaveClass('border-border')
  })
})
