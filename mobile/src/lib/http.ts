import { clearTokens, getTokens, saveTokens, type Tokens } from '@/lib/session';

// EXPO_PUBLIC_* ships inside the app, so this is an address, never a secret.
export const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'https://nesma-airlines-api.onrender.com';
const API_ROOT = `${API_URL}/api/v1/`;
const READ_TIMEOUT_MS = 30_000;

type Params = Record<string, string | number | boolean | undefined>;

interface Options {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  params?: Params;
  body?: unknown;
  signal?: AbortSignal;
}

export class HttpError extends Error {
  readonly status: number;
  readonly data: unknown;
  readonly code: string | undefined;
  readonly requestId: string | null;
  readonly retryAfter: number | null;

  constructor(status: number, message: string, data: unknown, headers: Headers) {
    super(message);
    this.status = status;
    this.data = data;
    this.code =
      typeof data === 'object' && data !== null && 'code' in data ? String(data.code) : undefined;
    this.requestId = headers.get('X-Request-ID');
    this.retryAfter = Number(headers.get('Retry-After')) || null;
  }
}

// Only these two 401s mean a stale token. The others, such as a wrong password, are final.
function isExpiredSession(error: unknown): boolean {
  return (
    error instanceof HttpError &&
    error.status === 401 &&
    (error.code === 'token_not_valid' || error.code === 'not_authenticated')
  );
}

// The API answers { detail, code }, or { field: [messages] } on a 400.
function readErrorMessage(data: unknown): string | undefined {
  if (typeof data !== 'object' || data === null) return undefined;
  if ('detail' in data && typeof data.detail === 'string') return data.detail;
  const first: unknown = Object.values(data).flat()[0];
  return typeof first === 'string' ? first : undefined;
}

function toQuery(params: Params = {}): string {
  const pairs = Object.entries(params).flatMap(([key, value]) =>
    value === undefined ? [] : [`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`],
  );
  return pairs.length ? `?${pairs.join('&')}` : '';
}

async function send<T>(endpoint: string, options: Options, access?: string): Promise<T> {
  const { method = 'GET', params, body, signal } = options;
  const controller = new AbortController();
  const cancel = () => controller.abort();
  signal?.addEventListener('abort', cancel);
  // Reads time out. Writes don't: aborting one the server is still running would report a
  // failure for work that happened, and an assistant answer can take 25 seconds.
  const timer = method === 'GET' ? setTimeout(cancel, READ_TIMEOUT_MS) : undefined;

  let response: Response;
  let data: unknown;
  try {
    response = await fetch(API_ROOT + endpoint + toQuery(params), {
      method,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(body !== undefined && { 'Content-Type': 'application/json' }),
        ...(access && { Authorization: `Bearer ${access}` }),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = await response.text();
    data = text && response.headers.get('content-type')?.includes('json') ? JSON.parse(text) : text;
  } catch (error) {
    // A query React Query cancelled stays an abort, so it isn't shown as a failure.
    if (signal?.aborted) throw error;
    // The friendly message hides the cause, so development builds print it in the Metro terminal.
    if (__DEV__) console.warn(`[http] ${endpoint}`, error);
    throw new Error(
      controller.signal.aborted
        ? 'The server took too long to respond. Please try again.'
        : "Can't reach the server. Check your connection and try again.",
    );
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', cancel);
  }

  if (response.ok) return data as T;
  throw new HttpError(
    response.status,
    readErrorMessage(data) ?? `Something went wrong (${response.status}).`,
    data,
    response.headers,
  );
}

let refreshing: Promise<void> | null = null;

// Each refresh retires the token it used, and a second use gets 401, so only one runs at a time.
function refreshTokens(): Promise<void> {
  refreshing ??= (async () => {
    const current = getTokens();
    if (!current) return;
    try {
      await saveTokens(
        await send<Tokens>('auth/mobile/refresh/', {
          method: 'POST',
          body: { refresh: current.refresh },
        }),
      );
    } catch (error) {
      // Only a refused refresh ends the session. Being offline keeps it for later.
      if (error instanceof HttpError && error.status === 401) await clearTokens();
      throw error;
    }
  })().finally(() => {
    refreshing = null;
  });
  return refreshing;
}

async function request<T>(endpoint: string, options: Options): Promise<T> {
  if (refreshing) await refreshing.catch(() => undefined);
  const used = getTokens()?.access;
  try {
    return await send<T>(endpoint, options, used);
  } catch (error) {
    if (!used || !isExpiredSession(error)) throw error;
  }
  // Another call may have refreshed while this one was in flight.
  if (getTokens()?.access === used) await refreshTokens();
  return send<T>(endpoint, options, getTokens()?.access);
}

type ReadOptions = Omit<Options, 'method' | 'body'>;

export const http = {
  get: <T>(endpoint: string, options?: ReadOptions) =>
    request<T>(endpoint, { ...options, method: 'GET' }),
  post: <T>(endpoint: string, body?: unknown) => request<T>(endpoint, { method: 'POST', body }),
  patch: <T>(endpoint: string, body: unknown) => request<T>(endpoint, { method: 'PATCH', body }),
  delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' }),
};

// For auth/register and auth/mobile/*: no bearer token, and nothing to refresh.
export function publicPost<T>(endpoint: string, body: unknown): Promise<T> {
  return send<T>(endpoint, { method: 'POST', body });
}

// Branch on this, never on the message: the API's `detail` text may change.
export function errorCode(error: unknown): string | undefined {
  return error instanceof HttpError ? error.code : undefined;
}

// A 500's request ID is how a report is matched to the server's logs, so every alert carries it.
export function errorMessage(error: unknown): string {
  if (error instanceof HttpError && error.status >= 500 && error.requestId) {
    return `${error.message} Reference: ${error.requestId}`;
  }
  return error instanceof Error ? error.message : String(error);
}

// A 400 with field problems is { field: ["message"] }; unreadable JSON has a detail instead.
export function fieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof HttpError) || error.status !== 400) return {};
  const { data } = error;
  if (typeof data !== 'object' || data === null || 'detail' in data) return {};
  return Object.fromEntries(
    Object.entries(data).map(([field, messages]) => [field, String([messages].flat()[0])]),
  );
}
