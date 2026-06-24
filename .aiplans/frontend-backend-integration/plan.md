# Conectar el frontend (Vercel) al backend real (Day 18 — Backend Integration)

## Contexto
El sitio en `parcerolegal.co` ya está deployado en Vercel con una UI completa (navbar,
search box, result panel, disclaimer, brand system documentado en `frontend/CLAUDE.md`),
pero `app/page.tsx` llama a `simulateQuery()` de `lib/mockData.ts` — datos 100% simulados.
Nunca se conectó al backend real en Railway, por eso "no se puede usar": cualquier pregunta
devuelve siempre la misma respuesta mock sobre el Artículo 15, sin importar la pregunta.

Esta tarea corresponde a **Day 18 (Backend Integration)** del board de Notion, que seguía
en Backlog. El backend (`POST /api/query`) ya está verificado funcionando en producción
(ver `.aiplans/migrate-jina-embeddings/` y `.aiplans/prompt-engineering-day12/`).

El shape real del backend (`backend/app/domain/entities.py`) es:
```
QueryResult: { answer: str, sources: Source[], out_of_scope: bool, processing_time_ms: float }
Source: { chunk_id: str, source_type: str, title: str, url: str }
```
Esto difiere del mock actual (`lib/types.ts`), que espera `type`, `excerpt`, `similarity` —
campos que el backend no devuelve. Se actualizan los tipos para reflejar la respuesta real.

## Cambios

### 1. `frontend/lib/types.ts`
Reemplazar `Source`/`QueryResponse` para que coincidan con el backend real:
```ts
export type SourceType = 'constitucion' | 'sentencia'

export interface Source {
  chunk_id: string
  source_type: SourceType
  title: string
  url: string
}

export interface QueryResponse {
  answer: string
  sources: Source[]
  out_of_scope: boolean
  processing_time_ms: number
}
```

### 2. `frontend/lib/api.ts` (nuevo)
Cliente de API con timeout (45s, ver `CLAUDE.md` raíz "Key Constraints") y manejo de
errores de red/HTTP, similar en espíritu al patrón `requests` + manejo de errores del
backend (`groq_llm.py`):
```ts
import type { QueryResponse } from './types'

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
```

### 3. `frontend/components/SourceCard.tsx` — rediseño a "Source pill"
Reemplazar la card con excerpt/score (datos que no existen) por el componente
**"Fuente / Source pill"** ya documentado en `frontend/CLAUDE.md` — link clickeable con
título, abre la fuente original (`source.url`) en una pestaña nueva:
```tsx
import type { Source } from '@/lib/types'

export function SourceCard({ source }: { source: Source }) {
  return (
    <a
      href={source.url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-1.5 text-xs font-semibold text-terra bg-terra-light border border-terra/12 px-3 py-1.5 rounded-lg hover:opacity-75 transition-opacity"
    >
      {source.title}
    </a>
  )
}
```

### 4. `frontend/components/ResultPanel.tsx`
Cambiar el contenedor de fuentes de `space-y-3` (cards apiladas) a `flex flex-wrap gap-1.5`
(fila de pills), acorde al patrón de uso de "Fuentes" mostrado en el brand system. El
`out_of_scope: true` no necesita manejo especial: el backend ya devuelve `sources: []` y un
`answer` explicando que está fuera de alcance — `ResultPanel` ya oculta la sección de
Fuentes cuando `hasSources` es falso, y el texto se renderiza igual via `ReactMarkdown`.

### 5. `frontend/components/ErrorState.tsx` (nuevo)
Mensaje simple para errores de red/timeout (no alucinaciones del LLM, sino fallas de
conexión). No usa `amber` — esa paleta está reservada exclusivamente para el disclaimer
legal según la regla #4 del brand system:
```tsx
export function ErrorState({ message }: { message: string }) {
  return (
    <div className="mt-8 text-center text-sm text-ink-2">
      <p>{message}</p>
    </div>
  )
}
```

### 6. `frontend/app/page.tsx`
- Importar `queryLegal`/`ApiError` de `lib/api` en vez de `simulateQuery` de `lib/mockData`.
- Agregar estado `error: string | null`.
- `handleSubmit`: try/catch — en éxito `setResponse(result)`; en `ApiError` hacer
  `setError(err.message)`; siempre limpiar el estado opuesto al iniciar.
- Renderizar `<ErrorState message={error} />` cuando `error` no es null y no está cargando.
- `EXAMPLE_QUERY` se mueve de `mockData.ts` a `types.ts` o queda como constante en
  `page.tsx` (mockData.ts deja de usarse y se elimina junto con su test si lo tuviera).

### 7. Tests
- `SourceCard.test.tsx`: reemplazar por tests del nuevo pill (título visible, `href`
  correcto, `target="_blank"`).
- `api.test.ts` (nuevo): mockear `global.fetch`, cubrir éxito, HTTP error, timeout/abort.
- `ErrorState.test.tsx` (nuevo): renderiza el mensaje recibido.
- Eliminar `lib/mockData.ts` si ya no se usa en ningún lado (confirmar con grep antes).

### 8. Variable de entorno (acción del usuario)
El usuario configurará manualmente en Vercel → Project Settings → Environment Variables:
```
NEXT_PUBLIC_API_URL=https://parcerolegal-production.up.railway.app
```
para Production (y opcionalmente Preview/Development), y luego redesplegará desde el
dashboard de Vercel. No se toca código de infraestructura para esto.

## Verificación
- `npm test` en `frontend/` — toda la suite debe pasar.
- `npm run build` para confirmar que compila sin errores de tipos.
- Smoke test local: `npm run dev` con `NEXT_PUBLIC_API_URL` apuntando al backend de Railway,
  probar una pregunta real y una fuera de alcance, confirmar que las fuentes son links
  clickeables válidos.
- Tras que el usuario configure la env var y redespliegue en Vercel: probar
  `https://parcerolegal.co` en el navegador con una pregunta real.
