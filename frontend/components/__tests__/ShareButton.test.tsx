import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ShareButton } from '../ShareButton'
import { createShare } from '@/lib/api'

jest.mock('@/lib/api', () => ({
  createShare: jest.fn(),
}))

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
    render(<ShareButton query="¿Qué es el habeas corpus?" />)

    expect(screen.getByRole('button', { name: /compartir/i })).toBeInTheDocument()
  })

  it('creates a share and copies the link on click', async () => {
    const user = userEvent.setup()
    mockClipboard()
    ;(createShare as jest.Mock).mockResolvedValue({ id: 'abc123' })

    render(<ShareButton query="¿Qué es el habeas corpus?" />)
    await user.click(screen.getByRole('button', { name: /compartir/i }))

    expect(createShare).toHaveBeenCalledWith('¿Qué es el habeas corpus?')
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(`${location.origin}/s/abc123`))
    expect(await screen.findByText(/link copiado/i)).toBeInTheDocument()
  })

  it('shows an error message when sharing fails', async () => {
    const user = userEvent.setup()
    mockClipboard()
    ;(createShare as jest.Mock).mockRejectedValue(new Error('boom'))

    render(<ShareButton query="¿Qué es el habeas corpus?" />)
    await user.click(screen.getByRole('button', { name: /compartir/i }))

    expect(await screen.findByText(/no se pudo compartir/i)).toBeInTheDocument()
  })
})
