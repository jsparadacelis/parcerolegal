# Implementation log — frontend-backend-integration

- 2026-06-24: Frontend en Vercel (parcerolegal.co) estaba deployado pero `app/page.tsx`
  llamaba a `simulateQuery()` (mock estático) — nunca se conectó al backend real. Implementado:
  - `lib/types.ts`: tipos actualizados al shape real del backend (`source_type`, `url`,
    `chunk_id`, `out_of_scope`; se quitan `excerpt`/`similarity` que el backend no devuelve).
  - `lib/api.ts` (nuevo): `queryLegal()` con timeout de 45s (AbortController) y `ApiError`
    para fallos de red/HTTP/timeout. TDD, 5 tests.
  - `components/SourceCard.tsx`: rediseñado de card con excerpt/score a "Source pill"
    clickeable (patrón ya documentado en `frontend/CLAUDE.md`), porque el backend no
    expone excerpt ni similarity score por fuente.
  - `components/ResultPanel.tsx`: contenedor de fuentes cambiado a `flex flex-wrap` de pills.
  - `components/ErrorState.tsx` (nuevo): mensaje de error de red/timeout, sin usar `amber`
    (reservado para el disclaimer legal).
  - `app/page.tsx`: reemplazado `simulateQuery` por `queryLegal` real, con estado `error`.
  - Eliminado `lib/mockData.ts` (sin más referencias).
  - Suite frontend: 31 tests pasando. `npm run build` sin errores de tipos.
  - Verificado con Playwright headless contra el backend real de Railway
    (`NEXT_PUBLIC_API_URL=https://parcerolegal-production.up.railway.app`): pregunta real
    ("¿qué es el habeas corpus?") devuelve respuesta correcta con pill de fuente clickeable
    (Art. 30, URL real de funcionpublica.gov.co); pregunta fuera de alcance (arepas) muestra
    el mensaje out_of_scope limpio, sin fuentes, sin errores de consola. Screenshot guardado.
  - Pendiente: usuario debe configurar `NEXT_PUBLIC_API_URL` en Vercel → Project Settings →
    Environment Variables (valor: `https://parcerolegal-production.up.railway.app`) y
    redesplegar desde el dashboard para que `parcerolegal.co` use el backend real.
