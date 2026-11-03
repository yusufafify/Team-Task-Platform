import { clsx } from 'clsx'
import type { ClassValue } from 'clsx'
import { extendTailwindMerge } from 'tailwind-merge'
import { HttpError } from '@/lib/http/errors'

// Register the custom scales (styles.css), so `text-heading-1` isn't mistaken for a text colour and
// a `shadow-card` passed to a component replaces its base shadow instead of both landing in the DOM.
const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      text: [
        'hero-display',
        'display-lg',
        'heading-1',
        'heading-2',
        'heading-3',
        'heading-4',
        'heading-5',
        'subtitle',
        'body-md',
        'body-sm',
        'caption',
        'caption-bold',
        'micro',
        'micro-uppercase',
        'button',
      ],
      shadow: ['subtle', 'card', 'mockup', 'modal'],
      spacing: ['section-sm', 'section', 'section-lg', 'hero'],
    },
  },
})

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function extractStatusCode(error: unknown): number {
  if (typeof error === 'object' && error !== null && 'status' in error) {
    const status = Number(error.status)
    return isNaN(status) ? 500 : status
  }
  return 500
}

export function extractErrorMessage(error: unknown): string {
  if (typeof error === 'object' && error !== null && 'message' in error) {
    return String(error.message)
  }
  return String(error)
}

// Branch on this, never on the message: the API's `detail` text may change.
export function extractErrorCode(error: unknown): string | undefined {
  return error instanceof HttpError ? error.code : undefined
}

export function extractRequestId(error: unknown): string | null {
  return error instanceof HttpError && error.status >= 500
    ? error.requestId
    : null
}

export function extractRetryAfter(error: unknown): number | null {
  return error instanceof HttpError ? error.retryAfter : null
}

// A 400 with field problems is { field: ["message"] }; unreadable JSON is a { detail, code } instead.
export function extractFieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof HttpError) || error.status !== 400) return {}
  const { data } = error
  if (typeof data !== 'object' || data === null || 'detail' in data) return {}
  return Object.fromEntries(
    Object.entries(data).map(([field, messages]) => [
      field,
      String([messages].flat()[0]),
    ]),
  )
}
