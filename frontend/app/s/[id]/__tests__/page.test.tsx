import { render, screen } from '@testing-library/react'
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

describe('SharedQueryPage', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('prefills the question and auto-submits when the share exists', async () => {
    ;(getShare as jest.Mock).mockResolvedValue({
      question: '¿Qué es el habeas corpus?',
      answer: 'Respuesta cacheada que no debe mostrarse directamente.',
      sources: [],
      out_of_scope: false,
    })
    ;(queryLegal as jest.Mock).mockResolvedValue({
      answer: 'Respuesta fresca del pipeline RAG.',
      sources: [],
      out_of_scope: false,
      processing_time_ms: 42,
    })

    render(<SharedQueryPage />)

    expect(await screen.findByDisplayValue('¿Qué es el habeas corpus?')).toBeInTheDocument()
    expect(queryLegal).toHaveBeenCalledWith('¿Qué es el habeas corpus?')
    expect(await screen.findByText(/Respuesta fresca del pipeline RAG/)).toBeInTheDocument()
    expect(screen.queryByText(/Respuesta cacheada/)).not.toBeInTheDocument()
  })

  it('falls back to the empty search state when the share is missing', async () => {
    ;(getShare as jest.Mock).mockResolvedValue(null)

    render(<SharedQueryPage />)

    await Promise.resolve()
    expect(screen.getByText(/Tu derecho, claro/)).toBeInTheDocument()
    expect(queryLegal).not.toHaveBeenCalled()
  })
})
