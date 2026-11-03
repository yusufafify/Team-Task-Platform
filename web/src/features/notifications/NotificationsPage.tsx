import { useNavigate } from '@tanstack/react-router'
import { Bell } from 'lucide-react'
import { Page } from '@/components/shared/Page'
import { EmptyState, ErrorState } from '@/components/shared/States'
import { Button } from '@/components/ui/button'
import { FormError } from '@/components/ui/field'
import { Skeleton } from '@/components/ui/skeleton'
import { useTeams } from '@/features/teams/query'
import { formatDayTime } from '@/lib/format'
import { cn, extractErrorMessage } from '@/lib/utils'
import {
  useMarkAllRead,
  useMarkRead,
  useNotifications,
  useUnreadCount,
} from './query'
import type { Notification } from './types'

interface NotificationRowProps {
  notification: Notification
}

function NotificationRow({ notification }: NotificationRowProps) {
  const { data: teams } = useTeams()
  const markRead = useMarkRead()
  const navigate = useNavigate()
  const isUnread = notification.read_at === null

  async function open() {
    if (isUnread) markRead.mutate(notification.id)
    if (notification.task !== null) {
      await navigate({
        to: '/tasks/$taskId',
        params: { taskId: notification.task },
      })
    } else if (notification.kind === 'report_ready') {
      // A report notification has no team id, only "<team name>: <month>" in its body.
      const team = teams?.find(({ name }) =>
        notification.body.startsWith(`${name}:`),
      )
      await (team
        ? navigate({
            to: '/teams/$teamId/reports',
            params: { teamId: team.id },
          })
        : navigate({ to: '/teams' }))
    }
  }

  return (
    <li>
      <button
        type="button"
        onClick={open}
        className="flex w-full flex-col gap-1 px-5 py-4 text-left transition-colors duration-150 hover-device:hover:bg-secondary"
      >
        <span className="flex items-baseline justify-between gap-3">
          <span
            className={cn(
              'text-body-sm',
              isUnread ? 'font-semibold' : 'text-muted-foreground',
            )}
          >
            {notification.title}
            {isUnread && <span className="sr-only"> (unread)</span>}
          </span>
          <span className="shrink-0 text-caption text-muted-foreground tabular-nums">
            {formatDayTime(notification.created_at)}
          </span>
        </span>
        <span className="text-body-sm text-muted-foreground">
          {notification.body}
        </span>
      </button>
    </li>
  )
}

export function NotificationsPage() {
  const {
    data,
    error,
    refetch,
    hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
  } = useNotifications()
  const { data: unread = 0 } = useUnreadCount()
  const markAll = useMarkAllRead()
  const notifications = data?.pages.flatMap((page) => page.results)

  return (
    <Page
      title="Notifications"
      action={
        unread > 0 && (
          <Button
            variant="outline"
            disabled={markAll.isPending}
            onClick={() => markAll.mutate()}
          >
            Mark all as read
          </Button>
        )
      }
    >
      <FormError>
        {markAll.error ? extractErrorMessage(markAll.error) : undefined}
      </FormError>
      {error ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : !notifications ? (
        <div aria-busy="true" className="flex flex-col gap-3">
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
        </div>
      ) : notifications.length === 0 ? (
        <EmptyState
          icon={Bell}
          title="Nothing here yet"
          message="You'll see new assignments, comments and due dates here as they happen."
        />
      ) : (
        <>
          <ul className="divide-y rounded-lg border">
            {notifications.map((notification) => (
              <NotificationRow
                key={notification.id}
                notification={notification}
              />
            ))}
          </ul>
          {hasNextPage && (
            <Button
              variant="outline"
              disabled={isFetchingNextPage}
              onClick={() => void fetchNextPage()}
              className="self-center"
            >
              Show older notifications
            </Button>
          )}
        </>
      )}
    </Page>
  )
}
