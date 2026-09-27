import type { QueryResponse, SharedQuery } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const TIMEOUT_MS = 45_000
const HTTP_SERVICE_UNAVAILABLE = 503
const GENERIC_ERROR_MESSAGE = 'No pudimos procesar tu pregunta. Intenta de nuevo en un momento.'

export class ApiError extends Error {}

// Solo el 503 trae un detail pensado para el usuario (saturación, timeout);
// otros errores pueden traer texto técnico que no debe mostrarse.
async function errorMessageFor(response: Response): Promise<string> {
  if (response.status !== HTTP_SERVICE_UNAVAILABLE) return GENERIC_ERROR_MESSAGE
  try {
    const body = await response.json()
    return typeof body?.detail === 'string' ? body.detail : GENERIC_ERROR_MESSAGE
  } catch {
    return GENERIC_ERROR_MESSAGE
  }
}

export async function queryLegal(question: string): Promise<QueryResponse> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS)

  try {
    const response = await fetch(`${API_URL}/api/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
      signal: controller.signal,
    })
    if (!response.ok) {
      throw new ApiError(await errorMessageFor(response))
    }
    return response.json()
  } catch (err) {
    if (err instanceof ApiError) throw err
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError('La consulta tardó demasiado. Intenta de nuevo.')
    }
    throw new ApiError('No pudimos conectar con el servidor. Revisa tu conexión e intenta de nuevo.')
  } finally {
    clearTimeout(timeoutId)
  }
}

export async function getShare(id: string): Promise<SharedQuery | null> {
  try {
    const response = await fetch(`${API_URL}/api/shares/${id}`)
    if (!response.ok) return null
    return response.json()
  } catch {
    return null
  }
}
