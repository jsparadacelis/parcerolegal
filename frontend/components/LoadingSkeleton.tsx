export function LoadingSkeleton() {
  return (
    <div className="mt-8" aria-busy="true" aria-live="polite">
      <p className="mb-6 text-center text-sm text-ink-3">
        Analizando legislación colombiana...
      </p>

      {/* Answer skeleton */}
      <div className="mb-6 space-y-3">
        <div className="h-4 w-full animate-pulse rounded bg-surface-3"></div>
        <div className="h-4 w-5/6 animate-pulse rounded bg-surface-3"></div>
        <div className="h-4 w-4/6 animate-pulse rounded bg-surface-3"></div>
      </div>

      {/* Sources skeleton */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink-3">Fuentes</h3>
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            data-testid="source-skeleton"
            className="animate-pulse rounded-lg border border-border p-4"
          >
            <div className="mb-2 h-4 w-2/3 rounded bg-surface-3"></div>
            <div className="h-3 w-1/3 rounded bg-surface-3"></div>
          </div>
        ))}
      </div>
    </div>
  )
}
