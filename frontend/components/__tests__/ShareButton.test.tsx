import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ShareButton } from '../ShareButton'

const writeText = jest.fn()

// userEvent.setup() instala su propio stub de navigator.clipboard, así que
// nuestro mock debe definirse después de llamarlo para no ser reemplazado.
function mockClipboard() {
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText },
    configurable: true,
  })
}

describe('ShareButton', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the share label', () => {
    render(<ShareButton shareToken="abc123" />)

    expect(screen.getByRole('button', { name: /compartir/i })).toBeInTheDocument()
  })

  it('copies the link built from the share token, with no network call', async () => {
    const user = userEvent.setup()
    mockClipboard()

    render(<ShareButton shareToken="abc123" />)
    await user.click(screen.getByRole('button', { name: /compartir/i }))

    expect(writeText).toHaveBeenCalledWith(`${location.origin}/s/abc123`)
    expect(await screen.findByText(/link copiado/i)).toBeInTheDocument()
  })

  it('shows an error message when the clipboard write fails', async () => {
    const user = userEvent.setup()
    writeText.mockRejectedValueOnce(new Error('denied'))
    mockClipboard()

    render(<ShareButton shareToken="abc123" />)
    await user.click(screen.getByRole('button', { name: /compartir/i }))

    expect(await screen.findByText(/no se pudo compartir/i)).toBeInTheDocument()
  })
})
