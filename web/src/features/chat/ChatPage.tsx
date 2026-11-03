import { MessagesSquare } from 'lucide-react'
import { Composer } from '@/components/shared/Composer'
import { ErrorState } from '@/components/shared/States'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useMe } from '@/features/auth/query'
import { displayName, formatDay, formatTime } from '@/lib/format'
import { useMessages, useSendMessage } from './query'
import type { Message } from './types'

const GROUP_WINDOW_MS = 5 * 60_000

function startsGroup(message: Message, previous?: Message) {
  if (!previous || previous.author.id !== message.author.id) return true
  const gap =
    new Date(message.created_at).getTime() -
    new Date(previous.created_at).getTime()
  return gap > GROUP_WINDOW_MS
}

interface MessageRowProps {
  message: Message
  previous?: Message
  isOwn: boolean
}

function MessageRow({ message, previous, isOwn }: MessageRowProps) {
  const day = formatDay(message.created_at)
  const newDay = !previous || formatDay(previous.created_at) !== day

  return (
    <li className="flex flex-col gap-1">
      {newDay && (
        <p className="py-3 text-center text-caption-bold text-muted-foreground">
          {day}
        </p>
      )}
      {(newDay || startsGroup(message, previous)) && (
        <p className="mt-3 flex items-baseline gap-2">
          <span className="text-body-sm font-medium">
            {isOwn ? 'You' : displayName(message.author)}
          </span>
          <span className="text-caption text-muted-foreground tabular-nums">
            {formatTime(message.created_at)}
          </span>
        </p>
      )}
      <p className="text-body-sm whitespace-pre-wrap">{message.body}</p>
    </li>
  )
}

interface ChatPageProps {
  teamId: number
}

export function ChatPage({ teamId }: ChatPageProps) {
  const me = useMe()
  const {
    data,
    error,
    refetch,
    hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
  } = useMessages(teamId)
  const send = useSendMessage(teamId)
  const messages = data?.pages.flatMap((page) => page.results).reverse()

  if (error) {
    return <ErrorState error={error} onRetry={() => void refetch()} />
  }

  return (
    <div className="flex h-[calc(100dvh-14rem)] min-h-80 flex-col rounded-lg border lg:h-[calc(100dvh-10.5rem)]">
      {/* column-reverse keeps the view on the newest message, and steady while older ones load. */}
      <div
        role="log"
        aria-label="Team chat"
        tabIndex={0}
        className="flex min-h-0 flex-1 flex-col-reverse overflow-y-auto p-4"
      >
        {!messages ? (
          <div aria-busy="true" className="flex flex-col gap-3">
            <Skeleton className="h-5 w-1/3" />
            <Skeleton className="h-5 w-2/3" />
            <Skeleton className="h-5 w-1/2" />
          </div>
        ) : messages.length === 0 ? (
          <div className="m-auto flex flex-col items-center gap-2 text-center">
            <MessagesSquare
              className="size-6 text-muted-foreground"
              aria-hidden="true"
            />
            <p className="text-body-sm text-muted-foreground">
              No messages yet. Say hello to the team.
            </p>
          </div>
        ) : (
          <div className="flex flex-col">
            {hasNextPage && (
              <Button
                variant="outline"
                size="sm"
                disabled={isFetchingNextPage}
                onClick={() => void fetchNextPage()}
                className="mb-2 self-center"
              >
                Show older messages
              </Button>
            )}
            <ul className="flex flex-col gap-1">
              {messages.map((message, index) => (
                <MessageRow
                  key={message.id}
                  message={message}
                  previous={messages[index - 1]}
                  isOwn={message.author.id === me.id}
                />
              ))}
            </ul>
          </div>
        )}
      </div>
      <Composer
        label="Write a message"
        submitLabel="Send"
        maxLength={5000}
        onSend={(body) => send.mutateAsync(body)}
      />
    </div>
  )
}
