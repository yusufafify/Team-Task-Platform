import { Sparkles } from 'lucide-react'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { Composer } from '@/components/shared/Composer'
import { ErrorState } from '@/components/shared/States'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { formatTime } from '@/lib/format'
import {
  extractErrorCode,
  extractErrorMessage,
  extractRetryAfter,
} from '@/lib/utils'
import { useAskAssistant, useAssistantThread, useClearThread } from './query'

function formatWait(seconds: number) {
  if (seconds < 90) return `${seconds} seconds`
  if (seconds < 5400) return `${Math.round(seconds / 60)} minutes`
  return `${Math.round(seconds / 3600)} hours`
}

function describeAskError(error: unknown) {
  const code = extractErrorCode(error)
  if (code === 'ai_unavailable') {
    return "The assistant isn't available right now. Your question is still in the box, so try again later."
  }
  if (code === 'throttled') {
    const wait = extractRetryAfter(error)
    return wait
      ? `You've reached the question limit. Try again in ${formatWait(wait)}.`
      : "You've reached the question limit. Try again later."
  }
  return extractErrorMessage(error)
}

interface AssistantPageProps {
  teamId: number
}

export function AssistantPage({ teamId }: AssistantPageProps) {
  const {
    data,
    error,
    refetch,
    hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
  } = useAssistantThread(teamId)
  const ask = useAskAssistant(teamId)
  const clear = useClearThread(teamId)
  const messages = data?.pages.flatMap((page) => page.results).reverse()

  if (error) {
    return <ErrorState error={error} onRetry={() => void refetch()} />
  }

  return (
    <div className="flex h-[calc(100dvh-14rem)] min-h-80 flex-col rounded-lg border lg:h-[calc(100dvh-10.5rem)]">
      <div className="flex shrink-0 items-center justify-between gap-3 border-b px-4 py-2">
        <p className="text-caption text-muted-foreground">
          Private to you. It remembers the last hour of this conversation.
        </p>
        {Boolean(messages?.length) && (
          <ConfirmDialog
            trigger={
              <Button variant="ghost" size="sm">
                New conversation
              </Button>
            }
            title="Start a new conversation?"
            message="This clears your conversation with the assistant for this team."
            confirmLabel="Clear conversation"
            onConfirm={() => clear.mutateAsync()}
          />
        )}
      </div>

      <div
        role="log"
        aria-label="Conversation with the assistant"
        tabIndex={0}
        className="flex min-h-0 flex-1 flex-col-reverse overflow-y-auto p-4"
      >
        {!messages ? (
          <div aria-busy="true" className="flex flex-col gap-3">
            <Skeleton className="h-5 w-1/3" />
            <Skeleton className="h-16" />
          </div>
        ) : messages.length === 0 && !ask.isPending ? (
          <div className="m-auto flex max-w-md flex-col items-center gap-2 text-center">
            <Sparkles
              className="size-6 text-muted-foreground"
              aria-hidden="true"
            />
            <p className="text-body-sm text-muted-foreground">
              Ask about this team&rsquo;s work, such as what&rsquo;s overdue or
              what&rsquo;s blocked. It only uses what you&rsquo;re allowed to
              see, and it can&rsquo;t change anything.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {hasNextPage && (
              <Button
                variant="outline"
                size="sm"
                disabled={isFetchingNextPage}
                onClick={() => void fetchNextPage()}
                className="self-center"
              >
                Show older messages
              </Button>
            )}
            {/* Answers can repeat what others wrote, so body is only ever rendered as text. */}
            <ul className="flex flex-col gap-4">
              {messages.map((message) => (
                <li key={message.id} className="flex flex-col gap-1">
                  <p className="flex items-baseline gap-2">
                    <span className="text-body-sm font-medium">
                      {message.role === 'user' ? 'You' : 'Assistant'}
                    </span>
                    <span className="text-caption text-muted-foreground tabular-nums">
                      {formatTime(message.created_at)}
                    </span>
                  </p>
                  <p className="text-body-sm whitespace-pre-wrap">
                    {message.body}
                  </p>
                </li>
              ))}
            </ul>
            {ask.isPending && (
              <div role="status" className="flex flex-col gap-2">
                <p className="text-body-sm text-muted-foreground">
                  Working on your answer. This can take up to 25 seconds.
                </p>
                <Skeleton className="h-5 w-2/3" />
              </div>
            )}
          </div>
        )}
      </div>

      <Composer
        label="Ask a question"
        submitLabel="Ask"
        maxLength={2000}
        onSend={(question) => ask.mutateAsync(question)}
        describeError={describeAskError}
      />
    </div>
  )
}
