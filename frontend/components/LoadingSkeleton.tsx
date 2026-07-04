export function LoadingSkeleton() {
  return (
    <div className="mt-8" aria-busy="true" aria-live="polite">
      {/* Respuesta del parcero (esqueleto) */}
      <div className="flex gap-3 items-start">
        {/* Avatar */}
        <div className="flex-none w-[34px] h-[34px] rounded-[10px] bg-surface-3 animate-pulse mt-0.5" />

        {/* Burbuja de respuesta */}
        <div className="flex-1 min-w-0 bg-surface border border-border rounded-[4px_16px_16px_16px] px-6 py-[22px]">
          {/* EN CORTO skeleton */}
          <div className="bg-surface-3 rounded-[11px] h-[64px] w-full animate-pulse mb-[18px]" />

          {/* Cuerpo skeleton */}
          <div className="space-y-[9px] mb-[22px]">
            <div className="h-3.5 w-[90%] animate-pulse rounded-[6px] bg-surface-3" />
            <div className="h-3.5 w-full animate-pulse rounded-[6px] bg-surface-3" />
            <div className="h-3.5 w-[70%] animate-pulse rounded-[6px] bg-surface-3" />
          </div>

          {/* Fuentes skeleton */}
          <div className="mb-1">
            <div className="mb-3 h-3 w-14 animate-pulse rounded-[6px] bg-surface-3" />
            <div className="flex flex-col gap-[9px]">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  data-testid="source-skeleton"
                  className="h-[52px] w-full animate-pulse rounded-[10px] bg-surface-3"
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      <p className="mt-4 text-center text-sm text-ink-3">
        Analizando legislación colombiana...
      </p>
    </div>
  )
}
