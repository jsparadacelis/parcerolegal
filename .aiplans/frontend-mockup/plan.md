# Task: Front-end Mockup (Iteración 0)

## Source
- PRD: `docs/prd.md` — Sección 4 (Flujo de Usuario), Sección 2.1 (Stack: Next.js + Vercel)
- Precede a: `.aiplans/scrape-constitucion/`
- Priority: 🔴 High | Estimate: 1-2 días

## Objective
Construir un front-end estático con datos *mock* que represente fielmente el producto final. Permite validar diseño, flujo de usuario y comunicar el valor del proyecto antes de tener el back-end funcional.

## Output
- `frontend/` — proyecto Next.js (App Router) con Tailwind CSS
- Sin integración real con API; datos hardcodeados en `lib/mockData.ts`

## Estructura de archivos
```
frontend/
├── app/
│   ├── layout.tsx          ← Layout global (fuente, meta tags)
│   ├── page.tsx            ← Página principal
│   └── globals.css
├── components/
│   ├── SearchBox.tsx
│   ├── ResultPanel.tsx
│   ├── SourceCard.tsx
│   ├── LoadingSkeleton.tsx
│   └── Disclaimer.tsx
├── lib/
│   └── mockData.ts         ← Respuesta y fuentes hardcodeadas
└── public/
    └── logo.svg
```

## Diseño / Paleta
| Token       | Color       | Uso                       |
|-------------|-------------|---------------------------|
| `primary`   | `#F5C518`   | CTAs, acentos             |
| `surface`   | `#0F172A`   | Fondo principal (dark)    |
| `surface-2` | `#1E293B`   | Cards, panels             |
| `text`      | `#F8FAFC`   | Texto principal           |
| `text-muted`| `#94A3B8`   | Subtextos, placeholders   |
| `accent`    | `#38BDF8`   | Links, fuentes            |

- Tipografía: **Inter** (Google Fonts)
- Dark mode por defecto

## Flujo simulado
1. Hero section + search box vacío
2. Usuario escribe pregunta (o hace clic en ejemplo predefinido)
3. Clic en "Preguntar" → `LoadingSkeleton` por ~1.5s (`setTimeout`)
4. `ResultPanel` con respuesta en markdown + `SourceCard`s
5. `Disclaimer` bajo la respuesta

## Mock Data
- Query de ejemplo: *"¿Puedo grabar una llamada sin permiso de la otra persona?"*
- Fuentes mock: Constitución Art. 15 + Sentencia T-881/2002

## Implementation Approach
- `npx create-next-app` con TypeScript, Tailwind, App Router
- `react-markdown` para renderizar la respuesta
- Sin llamadas a API externas
- Responsive: desktop + mobile (375px)

## Scope
### Incluye
- Hero, search box, resultado mock, tarjetas de fuentes, disclaimer, navbar mínima

### No incluye
- Integración con backend real
- Autenticación, analytics, historial
