import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchBox } from '../SearchBox'

describe('SearchBox', () => {
  it('renders input with placeholder text', () => {
    render(<SearchBox onSubmit={jest.fn()} />)

    expect(
      screen.getByPlaceholderText(/pregunta sobre.*legislación/i)
    ).toBeInTheDocument()
  })

  it('renders submit button with appropriate text', () => {
    render(<SearchBox onSubmit={jest.fn()} />)

    expect(
      screen.getByRole('button', { name: /preguntar/i })
    ).toBeInTheDocument()
  })

  it('calls onSubmit with query when form is submitted', async () => {
    const user = userEvent.setup()
    const handleSubmit = jest.fn()
    render(<SearchBox onSubmit={handleSubmit} />)

    const input = screen.getByRole('textbox')
    await user.type(input, '¿Puedo grabar una llamada?')
    await user.click(screen.getByRole('button', { name: /preguntar/i }))

    expect(handleSubmit).toHaveBeenCalledWith('¿Puedo grabar una llamada?')
  })

  it('does not submit when query is empty', async () => {
    const user = userEvent.setup()
    const handleSubmit = jest.fn()
    render(<SearchBox onSubmit={handleSubmit} />)

    await user.click(screen.getByRole('button', { name: /preguntar/i }))

    expect(handleSubmit).not.toHaveBeenCalled()
  })

  it('clears input after successful submission', async () => {
    const user = userEvent.setup()
    const handleSubmit = jest.fn()
    render(<SearchBox onSubmit={handleSubmit} />)

    const input = screen.getByRole('textbox') as HTMLInputElement
    await user.type(input, 'test query')
    await user.click(screen.getByRole('button', { name: /preguntar/i }))

    expect(input.value).toBe('')
  })

  it('disables submit button when loading', () => {
    render(<SearchBox onSubmit={jest.fn()} isLoading={true} />)

    expect(
      screen.getByRole('button', { name: /preguntar/i })
    ).toBeDisabled()
  })

  it('disables input when loading', () => {
    render(<SearchBox onSubmit={jest.fn()} isLoading={true} />)

    expect(screen.getByRole('textbox')).toBeDisabled()
  })
})
