import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import {
  extractErrorMessage,
  extractRequestId,
  extractStatusCode,
} from '@/lib/utils'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  message: string
  action?: ReactNode
}

export function EmptyState({
  icon: Icon,
  title,
  message,
  action,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed px-6 py-section-sm text-center">
      <span className="flex size-12 items-center justify-center rounded-lg bg-secondary text-muted-foreground">
        <Icon className="size-6" aria-hidden="true" />
      </span>
      <h2 className="text-heading-5">{title}</h2>
      <p className="max-w-md text-body-sm text-muted-foreground">{message}</p>
      {action}
    </div>
  )
}

interface ErrorStateProps {
  error: unknown
  onRetry?: () => void
}

export function ErrorState({ error, onRetry }: ErrorStateProps) {
  const requestId = extractRequestId(error)
  // The API answers 404 for anything hidden from this person, so retrying can't help.
  const isMissing = extractStatusCode(error) === 404

  return (
    <div
      role="alert"
      className="flex flex-col items-start gap-2 rounded-lg border px-6 py-5"
    >
      <h2 className="text-heading-5">
        {isMissing ? "This isn't available" : "This couldn't load"}
      </h2>
      <p className="text-body-sm text-muted-foreground">
        {isMissing
          ? 'It may have been deleted, or you may not have access to it.'
          : extractErrorMessage(error)}
      </p>
      {requestId && (
        <p className="text-caption text-muted-foreground">
          Reference: {requestId}
        </p>
      )}
      {onRetry && !isMissing && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  )
}
