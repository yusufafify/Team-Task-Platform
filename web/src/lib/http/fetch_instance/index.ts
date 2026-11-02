import { BASE_URL } from '../const'
import { HttpError } from '../errors'

const READ_TIMEOUT_MS = 30_000

interface FetchOptions extends Omit<RequestInit, 'body'> {
  // undefined values are skipped, so optional filters can be passed as-is.
  params?: Record<string, string | number | boolean | undefined>
  body?: unknown
}

async function request<T>(
  endpoint: string,
  options: FetchOptions = {},
): Promise<T> {
  const { params, body, ...customConfig } = options

  // If BASE_URL is empty, the request goes to the current origin.
  const url = new URL(endpoint, BASE_URL || window.location.origin)
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

    const payload = (data ?? {}) as {
      message?: string | Array<string>
      error?: string
    }
    const errorMessage =
      [payload.message].flat()[0] ||
      payload.error ||
      response.statusText ||
      'An error occurred'
    throw new HttpError(response.status, errorMessage, data)
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
      error instanceof Error ? error.message : 'Network request failed',
      { cause: error },
    )
  }
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
