import { clsx } from 'clsx'
import type { ClassValue } from 'clsx'
import { extendTailwindMerge } from 'tailwind-merge'

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
