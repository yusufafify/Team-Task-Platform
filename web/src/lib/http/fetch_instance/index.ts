import { API_ROOT, BASE_URL } from '../const'
import { HttpError, isExpiredSession } from '../errors'

const READ_TIMEOUT_MS = 30_000

interface FetchOptions extends Omit<RequestInit, 'body'> {
  // undefined values are skipped, so optional filters can be passed as-is.
  params?: Record<string, string | number | boolean | undefined>
  body?: unknown
}

// The API answers with { detail, code }, or with { field: [messages] } on a 400.
function readErrorMessage(data: unknown): string | undefined {
  if (typeof data !== 'object' || data === null) return undefined
  if ('detail' in data && typeof data.detail === 'string') return data.detail
  const first: unknown = Object.values(data).flat()[0]
  return typeof first === 'string' ? first : undefined
}

async function send<T>(
  endpoint: string,
  options: FetchOptions = {},
): Promise<T> {
  const { params, body, ...customConfig } = options

  // If BASE_URL is empty, the request goes to the current origin.
  const url = new URL(API_ROOT + endpoint, BASE_URL || window.location.origin)
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined) url.searchParams.append(key, String(value))
  })

  // Reads get a timeout. Writes don't: aborting one the server is still processing
  // would report a failure for work that actually happened.
  const isRead = !customConfig.method || customConfig.method === 'GET'
  const signal = isRead
    ? AbortSignal.any([
        AbortSignal.timeout(READ_TIMEOUT_MS),
        ...(customConfig.signal ? [customConfig.signal] : []),
      ])
    : customConfig.signal

  const isFormData = body instanceof FormData

  try {
    const response = await fetch(url, {
      ...customConfig,
      signal,
      // Sends HTTP-only cookies to the external backend on every request.
      credentials: 'include',
      headers: {
        // FormData needs the browser to set its own multipart boundary.
        ...(!isFormData && { 'Content-Type': 'application/json' }),
        ...customConfig.headers,
      },
      body: isFormData
        ? body
        : body === undefined
          ? undefined
          : JSON.stringify(body),
    })

    const isJson = response.headers
      .get('content-type')
      ?.includes('application/json')
    const data: unknown = await (isJson ? response.json() : response.text())

    if (response.ok) {
      return data as T
    }

    const errorMessage =
      readErrorMessage(data) || response.statusText || 'An error occurred'
    throw new HttpError(response.status, errorMessage, data, response.headers)
  } catch (error) {
    if (error instanceof HttpError) {
      throw error
    }
    // A cancelled query (React Query's signal) must stay an AbortError so it's recognised as one.
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw error
    }
    if (error instanceof DOMException && error.name === 'TimeoutError') {
      throw new Error(
        'The server took too long to respond. Please try again.',
        {
          cause: error,
        },
      )
    }
    // Otherwise it's a network error (e.g., CORS, offline).
    throw new Error(
      "Can't reach the server. Check your connection and try again.",
      { cause: error },
    )
  }
}

let refreshing: Promise<void> | null = null

// Refresh tokens rotate, so a tab must never run two refreshes at once.
function refreshSession(): Promise<void> {
  refreshing ??= send<void>('auth/refresh/', { method: 'POST' }).finally(() => {
    refreshing = null
  })
  return refreshing
}

async function request<T>(
  endpoint: string,
  options: FetchOptions = {},
): Promise<T> {
  if (refreshing) await refreshing.catch(() => undefined)

  try {
    return await send<T>(endpoint, options)
  } catch (error) {
    if (!isExpiredSession(error)) throw error
  }

  await refreshSession().catch((error: unknown) => {
    // A 401 can mean another tab just rotated the token, so the retry below still runs.
    if (!(error instanceof HttpError && error.status === 401)) throw error
  })
  return send<T>(endpoint, options)
}

export const http = {
  get: <T>(endpoint: string, options?: Omit<FetchOptions, 'method' | 'body'>) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(
    endpoint: string,
    body?: unknown,
    options?: Omit<FetchOptions, 'method' | 'body'>,
  ) => request<T>(endpoint, { ...options, method: 'POST', body }),

  put: <T>(
    endpoint: string,
    body?: unknown,
    options?: Omit<FetchOptions, 'method' | 'body'>,
  ) => request<T>(endpoint, { ...options, method: 'PUT', body }),

  patch: <T>(
    endpoint: string,
    body?: unknown,
    options?: Omit<FetchOptions, 'method' | 'body'>,
  ) => request<T>(endpoint, { ...options, method: 'PATCH', body }),

  delete: <T>(
    endpoint: string,
    options?: Omit<FetchOptions, 'method' | 'body'>,
  ) => request<T>(endpoint, { ...options, method: 'DELETE' }),
}
