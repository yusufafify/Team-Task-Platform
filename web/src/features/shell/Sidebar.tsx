import { Link } from '@tanstack/react-router'
import { Bell, ListChecks, Plus, User } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import ThemeToggle from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { useMe } from '@/features/auth/query'
import { useUnreadCount } from '@/features/notifications/query'
import { useTeams } from '@/features/teams/query'
import { displayName } from '@/lib/format'

const NAV_LINK =
  'flex h-11 items-center gap-3 rounded-sm px-3 text-body-sm font-medium text-muted-foreground transition-colors duration-150 hover-device:hover:bg-secondary hover-device:hover:text-foreground data-[status=active]:bg-secondary data-[status=active]:text-foreground lg:h-9'

interface SidebarProps {
  onNavigate?: () => void
}

interface MainLinkProps extends SidebarProps {
  to: '/' | '/notifications'
  icon: LucideIcon
  label: string
  badge?: number
}

function MainLink({ to, icon: Icon, label, badge, onNavigate }: MainLinkProps) {
  return (
    <Link
      to={to}
      onClick={onNavigate}
      activeOptions={{ exact: true }}
      className={NAV_LINK}
    >
      <Icon className="size-4" aria-hidden="true" />
      <span className="flex-1">{label}</span>
      {badge ? (
        <span className="rounded-full bg-secondary px-2 text-caption-bold tabular-nums text-foreground">
          {badge}
          <span className="sr-only"> unread</span>
        </span>
      ) : null}
    </Link>
  )
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const user = useMe()
  const { data: teams } = useTeams()
  const { data: unread } = useUnreadCount()

  return (
    <div className="flex h-full min-h-0 flex-col gap-6 p-3">
      <Link
        to="/"
        onClick={onNavigate}
        className="px-3 pt-2 text-heading-5 text-foreground"
      >
        Nesma Airlines
      </Link>

      <nav aria-label="Main" className="flex flex-col gap-1">
        <MainLink
          to="/"
          icon={ListChecks}
          label="Tasks"
          onNavigate={onNavigate}
        />
        <MainLink
          to="/notifications"
          icon={Bell}
          label="Notifications"
          badge={unread}
          onNavigate={onNavigate}
        />
      </nav>

      <nav
        aria-label="Teams"
        className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto"
      >
        <div className="flex items-center justify-between pr-1 pl-3">
          <Link
            to="/teams"
            onClick={onNavigate}
            activeOptions={{ exact: true }}
            className="text-caption-bold text-muted-foreground hover-device:hover:text-foreground"
          >
            Teams
          </Link>
          <Button
            asChild
            variant="ghost"
            size="icon"
            className="size-11 text-muted-foreground lg:size-8"
          >
            <Link to="/teams" onClick={onNavigate} aria-label="New team">
              <Plus aria-hidden="true" />
            </Link>
          </Button>
        </div>
        {teams?.map((team) => (
          <Link
            key={team.id}
            to="/teams/$teamId"
            params={{ teamId: team.id }}
            onClick={onNavigate}
            className={NAV_LINK}
          >
            <span className="truncate">{team.name}</span>
          </Link>
        ))}
      </nav>

      <div className="flex items-center gap-1 border-t pt-3">
        <Link
          to="/account"
          onClick={onNavigate}
          className={`${NAV_LINK} min-w-0 flex-1`}
        >
          <User className="size-4 shrink-0" aria-hidden="true" />
          <span className="truncate">{displayName(user)}</span>
        </Link>
        <ThemeToggle />
      </div>
    </div>
  )
}
