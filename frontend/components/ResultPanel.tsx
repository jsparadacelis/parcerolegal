import ReactMarkdown from 'react-markdown'
import type { QueryResponse } from '@/lib/types'
import { SourceCard } from './SourceCard'
import { Disclaimer } from './Disclaimer'

interface ResultPanelProps {
  response: QueryResponse
  /** Pregunta que originó la respuesta (para la burbuja del usuario). Opcional. */
  query?: string
}

// Etiqueta mono de sección: EN CORTO / PUNTOS CLAVE / FUENTES
function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-mono font-bold text-[10.5px] tracking-[0.12em] text-ink-3 mb-3">
      {children}
    </p>
  )
}

export function ResultPanel({ response, query }: ResultPanelProps) {
  const hasSources = response.sources.length > 0

  // Heurística: el 1er párrafo del markdown se renderiza como bloque "EN CORTO".
  // Los <ul>/<li> se agrupan bajo "PUNTOS CLAVE" con check.
  // (Recomendación futura: que la API devuelva tl_dr y key_points aparte.)
  let pIndex = 0

  return (
    <div className="mt-8">
      {/* Pregunta del usuario */}
      {query && (
        <div className="flex justify-end mb-5">
          <div className="bg-primary text-white text-sm leading-snug font-medium px-4 py-[11px] rounded-[14px_14px_3px_14px] max-w-[78%]">
            {query}
          </div>
        </div>
      )}

      {/* Respuesta del parcero */}
      <div className="flex gap-3 items-start">
        {/* Avatar */}
        <div className="flex-none w-[34px] h-[34px] rounded-[10px] bg-primary relative flex items-center justify-center mt-0.5">
          <span className="font-display font-extrabold text-[16px] text-white leading-none">p</span>
          <span className="absolute top-[7px] right-[7px] w-[5px] h-[5px] rounded-full bg-gold" />
        </div>

        {/* Burbuja de respuesta */}
        <div className="flex-1 min-w-0 bg-surface border border-border rounded-[4px_16px_16px_16px] px-6 py-[22px]">
          <ReactMarkdown
            components={{
              p: ({ children }) => {
                const i = pIndex++
                if (i === 0) {
                  // Bloque EN CORTO (TL;DR)
                  return (
                    <div className="bg-primary-tint rounded-[11px] px-4 py-[14px] mb-[18px]">
                      <p className="font-mono font-bold text-[10.5px] tracking-[0.12em] text-primary mb-1.5">
                        EN CORTO
                      </p>
                      <p className="text-base leading-normal font-medium text-ink">{children}</p>
                    </div>
                  )
                }
                return <p className="mb-[18px] text-[15px] leading-[1.7] text-ink-2">{children}</p>
              },
              strong: ({ children }) => (
                <strong className="font-semibold text-ink">{children}</strong>
              ),
              em: ({ children }) => <em className="italic text-ink-3">{children}</em>,
              ul: ({ children }) => (
                <div className="mb-[22px]">
                  <SectionLabel>PUNTOS CLAVE</SectionLabel>
                  <div className="flex flex-col gap-3">{children}</div>
                </div>
              ),
              ol: ({ children }) => (
                <div className="mb-[22px]">
                  <SectionLabel>PUNTOS CLAVE</SectionLabel>
                  <div className="flex flex-col gap-3">{children}</div>
                </div>
              ),
              li: ({ children }) => (
                <div className="flex gap-[11px] items-start">
                  <span className="flex-none w-5 h-5 rounded-full bg-primary-tint text-primary flex items-center justify-center text-[11px] font-bold mt-px">
                    ✓
                  </span>
                  <span className="text-[14.5px] leading-[1.55] text-ink-2">{children}</span>
                </div>
              ),
            }}
          >
            {response.answer}
          </ReactMarkdown>

          {/* Fuentes */}
          {hasSources && (
            <div className="mb-1">
              <SectionLabel>FUENTES</SectionLabel>
              <div className="flex flex-col gap-[9px]">
                {response.sources.map((source) => (
                  <SourceCard key={source.chunk_id} source={source} />
                ))}
              </div>
            </div>
          )}

          {/* Disclaimer integrado */}
          <Disclaimer />
        </div>
      </div>
    </div>
  )
}
