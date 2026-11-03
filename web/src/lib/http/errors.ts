export class HttpError extends Error {
  public status: number
  public data: unknown
  public code: string | undefined
  public requestId: string | null
  public retryAfter: number | null

  constructor(
    status: number,
    message: string,
    data?: unknown,
    headers?: Headers,
  ) {
    super(message)
    this.status = status
    this.data = data
    this.code =
      typeof data === 'object' && data !== null && 'code' in data
        ? String(data.code)
        : undefined
    this.requestId = headers?.get('X-Request-ID') ?? null
    this.retryAfter = Number(headers?.get('Retry-After')) || null
  }
}

// Only these two 401s mean a stale session. The others, such as a wrong password, are final.
export function isExpiredSession(error: unknown): boolean {
  return (
    error instanceof HttpError &&
    error.status === 401 &&
    (error.code === 'token_not_valid' || error.code === 'not_authenticated')
  )
}

// A full page load, so the next person on this browser inherits no cached data.
export function endExpiredSession(error: unknown) {
  if (!isExpiredSession(error)) return
  const here = window.location.pathname + window.location.search
  window.location.assign(`/login?redirect=${encodeURIComponent(here)}`)
}
