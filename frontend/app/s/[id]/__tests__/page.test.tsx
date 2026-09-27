import { render, screen, fireEvent } from '@testing-library/react'
import SharedQueryPage from '../page'
import { queryLegal, getShare } from '@/lib/api'

jest.mock('next/navigation', () => ({
  useParams: () => ({ id: 'abc123' }),
}))

jest.mock('@/lib/api', () => ({
  queryLegal: jest.fn(),
  getShare: jest.fn(),
  ApiError: class ApiError extends Error {},
}))

const SHARED = {
  question: '¿Qué es el habeas corpus?',
  answer: 'Respuesta guardada al momento de compartir.',
  sources: [
    {
      chunk_id: 'const-30',
      source_type: 'constitucion' as const,
      title: 'Artículo 30',
      url: 'https://example.com/art30',
    },
  ],
  out_of_scope: false,
}

describe('SharedQueryPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders the stored answer, question and sources without calling the RAG', async () => {
    ;(getShare as jest.Mock).mockResolvedValue(SHARED)

    render(<SharedQueryPage />)

    expect(await screen.findByText(/Respuesta guardada al momento de compartir/)).toBeInTheDocument()
    // Pregunta como burbuja del usuario
    expect(screen.getByText('¿Qué es el habeas corpus?')).toBeInTheDocument()
    expect(screen.getByText('Artículo 30')).toBeInTheDocument()
    expect(getShare).toHaveBeenCalledWith('abc123')
    expect(queryLegal).not.toHaveBeenCalled()
  })

  it('renders an out-of-scope stored answer without sources and without calling the RAG', async () => {
    ;(getShare as jest.Mock).mockResolvedValue({
      question: '¿Cómo hago una torta?',
      answer: 'Esa pregunta está fuera de lo que puedo responder.',
      sources: [],
      out_of_scope: true,
    })

    render(<SharedQueryPage />)

    expect(await screen.findByText(/fuera de lo que puedo responder/)).toBeInTheDocument()
    expect(screen.queryByText('FUENTES')).not.toBeInTheDocument()
    expect(queryLegal).not.toHaveBeenCalled()
  })

  it('calls the RAG only when the user submits a new question', async () => {
    ;(getShare as jest.Mock).mockResolvedValue(SHARED)
    ;(queryLegal as jest.Mock).mockResolvedValue({
      answer: 'Respuesta fresca del pipeline RAG.',
      sources: [],
      out_of_scope: false,
      processing_time_ms: 42,
      share_token: 'nuevo',
    })

    render(<SharedQueryPage />)
    await screen.findByText(/Respuesta guardada al momento de compartir/)
    expect(queryLegal).not.toHaveBeenCalled()

    const input = screen.getByRole('textbox')
    fireEvent.change(input, { target: { value: '¿Qué es la tutela?' } })
    fireEvent.submit(input.closest('form')!)

    expect(await screen.findByText(/Respuesta fresca del pipeline RAG/)).toBeInTheDocument()
    expect(queryLegal).toHaveBeenCalledWith('¿Qué es la tutela?')
    expect(screen.queryByText(/Respuesta guardada al momento de compartir/)).not.toBeInTheDocument()
  })

  it('shows an error state when the share is missing', async () => {
    ;(getShare as jest.Mock).mockResolvedValue(null)

    render(<SharedQueryPage />)

    expect(await screen.findByText(/No encontramos esta consulta compartida/)).toBeInTheDocument()
    expect(queryLegal).not.toHaveBeenCalled()
  })
})
