interface ErrorStateProps {
  message: string
}

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="mt-8 rounded-[12px] border border-border bg-surface p-4 sm:p-5">
      <div className="flex items-start gap-3">
        <div className="flex-none w-[30px] h-[30px] rounded-full bg-error-tint text-error flex items-center justify-center font-bold text-[15px] mt-0.5">
          !
        </div>
        <p className="text-[13.5px] leading-[1.5] text-ink-2">{message}</p>
      </div>
    </div>
  )
}
