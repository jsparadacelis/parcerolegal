export function LoadingSkeleton() {
  return (
    <div className="mt-8" aria-busy="true" aria-live="polite">
      <div className="bg-terra-pale rounded-2xl p-4 sm:p-5 border border-terra-border">
        {/* Answer skeleton */}
        <div className="mb-4 space-y-2.5">
          <div className="h-3.5 w-full animate-pulse rounded bg-terra-border" />
          <div className="h-3.5 w-5/6 animate-pulse rounded bg-terra-border" />
          <div className="h-3.5 w-full animate-pulse rounded bg-terra-border" />
          <div className="h-3.5 w-4/6 animate-pulse rounded bg-terra-border" />
          <div className="h-3.5 w-full animate-pulse rounded bg-terra-border" />
          <div className="h-3.5 w-3/5 animate-pulse rounded bg-terra-border" />
        </div>

        {/* Sources skeleton */}
        <div className="mb-4">
          <div className="mb-2.5 h-3 w-10 animate-pulse rounded bg-terra-border" />
          <div className="flex flex-wrap gap-1.5">
            {[80, 112, 64].map((w, i) => (
              <div
                key={i}
                data-testid="source-skeleton"
                className="h-8 animate-pulse rounded-lg bg-terra-border"
                style={{ width: w }}
              />
            ))}
          </div>
        </div>

        {/* Disclaimer skeleton */}
        <div className="h-8 animate-pulse rounded-r-lg bg-terra-border border-l-[3px] border-amber/30" />
      </div>

      <p className="mt-4 text-center text-sm text-ink-3">
        Analizando legislación colombiana...
      </p>
    </div>
  )
}
