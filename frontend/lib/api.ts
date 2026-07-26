import type { QueryResponse, SharedQuery } from './types'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const TIMEOUT_MS = 45_000

export class ApiError extends Error {}

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
      throw new ApiError('No pudimos procesar tu pregunta. Intenta de nuevo en un momento.')
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
