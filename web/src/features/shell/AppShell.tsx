import { useEffect, useState } from 'react'
import { Link, Outlet, useLocation } from '@tanstack/react-router'
import { useQueryClient } from '@tanstack/react-query'
import { Bell, Menu, WifiOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useLiveSocket } from '@/features/live/hooks'
import {
  unreadCountQuery,
  useUnreadCount,
} from '@/features/notifications/query'
import { Sidebar } from './Sidebar'

function MobileBar() {
  const [open, setOpen] = useState(false)
  const { data: unread } = useUnreadCount()

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b px-1 lg:hidden">
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="Open menu">
            <Menu aria-hidden="true" />
          </Button>
        </DialogTrigger>
        <DialogContent className="top-0 left-0 h-dvh max-h-dvh w-72 max-w-[85vw] translate-x-0 translate-y-0 gap-0 rounded-none border-y-0 border-l-0 bg-surface-soft p-0">
          <DialogTitle className="sr-only">Menu</DialogTitle>
          <DialogDescription className="sr-only">
            Move between tasks, notifications, teams and your account.
          </DialogDescription>
          <Sidebar onNavigate={() => setOpen(false)} />
        </DialogContent>
      </Dialog>

      <Link to="/" className="flex h-11 items-center text-heading-5">
        Nesma Airlines
      </Link>

      <Button asChild variant="ghost" size="icon" className="relative">
        <Link
          to="/notifications"
          aria-label={
            unread ? `Notifications, ${unread} unread` : 'Notifications'
          }
        >
          <Bell aria-hidden="true" />
          {unread ? (
            <span
              aria-hidden="true"
              className="absolute top-1 right-1 rounded-full bg-inverse px-1.5 text-micro tabular-nums text-inverse-foreground"
            >
              {unread}
            </span>
          ) : null}
        </Link>
      </Button>
    </header>
  )
}

export function AppShell() {
  const { isDown } = useLiveSocket()
  const queryClient = useQueryClient()
  const { pathname } = useLocation()

  useEffect(() => {
    void queryClient.invalidateQueries({
      queryKey: unreadCountQuery.queryKey,
    })
  }, [pathname, queryClient])

  return (
    <div className="flex h-dvh flex-col lg:flex-row">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-card focus:px-4 focus:py-2"
      >
        Skip to content
      </a>
      <aside className="hidden w-64 shrink-0 border-r bg-surface-soft lg:block">
        <Sidebar />
      </aside>
      <MobileBar />
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        {isDown && (
          <p
            role="status"
            className="flex shrink-0 items-center gap-2 bg-tint-peach px-4 py-2 text-body-sm text-on-tint sm:px-8"
          >
            <WifiOff className="size-4 shrink-0" aria-hidden="true" />
            Live updates are paused, so new messages may be slow to appear.
            Reconnecting.
          </p>
        )}
        <main
          id="main"
          tabIndex={-1}
          className="min-h-0 flex-1 overflow-y-auto"
        >
          <Outlet />
        </main>
      </div>
    </div>
  )
}
