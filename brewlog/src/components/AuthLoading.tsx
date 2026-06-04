export function AuthLoading({ message = "Checking session..." }: { message?: string }) {
  return (
    <div
      className="mx-auto mt-16 max-w-md rounded-lg border px-6 py-5 text-center text-sm"
      role="status"
      style={{
        backgroundColor: 'var(--card)',
        borderColor: 'var(--border-color)',
        color: 'var(--text-muted)',
      }}
    >
      {message}
    </div>
  )
}
