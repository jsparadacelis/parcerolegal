interface ErrorStateProps {
  message: string
}

export function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="mt-8 text-center text-sm text-ink-2">
      <p>{message}</p>
    </div>
  )
}
