import { queryLegal, ApiError } from '../api'

describe('queryLegal', () => {
  beforeEach(() => {
    global.fetch = jest.fn()
  })

  afterEach(() => {
    jest.restoreAllMocks()
  })

  it('returns the parsed response on success', async () => {
    const mockResponse = {
      answer: 'El habeas corpus protege la libertad.',
      sources: [],
      out_of_scope: false,
      processing_time_ms: 100,
    }
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    })

    const result = await queryLegal('¿Qué es el habeas corpus?')

    expect(result).toEqual(mockResponse)
  })

  it('sends the question in the request body', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ answer: '', sources: [], out_of_scope: false, processing_time_ms: 0 }),
    })

    await queryLegal('¿Qué es el habeas corpus?')

    const [, options] = (global.fetch as jest.Mock).mock.calls[0]
    expect(JSON.parse(options.body)).toEqual({ question: '¿Qué es el habeas corpus?' })
  })

  it('throws ApiError when the response is not ok', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({ ok: false, json: async () => ({}) })

    await expect(queryLegal('pregunta')).rejects.toThrow(ApiError)
  })

  it('throws ApiError when fetch rejects (network failure)', async () => {
    ;(global.fetch as jest.Mock).mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(queryLegal('pregunta')).rejects.toThrow(ApiError)
  })

  it('throws ApiError with a timeout message when the request is aborted', async () => {
    ;(global.fetch as jest.Mock).mockRejectedValue(
      new DOMException('The operation was aborted.', 'AbortError')
    )

    await expect(queryLegal('pregunta')).rejects.toThrow('tardó demasiado')
  })
})
