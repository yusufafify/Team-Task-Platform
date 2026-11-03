import { Link, Outlet } from '@tanstack/react-router'
import { Badge } from '@/components/ui/badge'
import { useTeam } from './query'

const TABS = [
  { to: '/teams/$teamId', label: 'Tasks', exact: true },
  { to: '/teams/$teamId/chat', label: 'Chat' },
  { to: '/teams/$teamId/assistant', label: 'Assistant' },
  { to: '/teams/$teamId/stats', label: 'Stats' },
  { to: '/teams/$teamId/reports', label: 'Reports', leaderOnly: true },
  { to: '/teams/$teamId/members', label: 'Members' },
  { to: '/teams/$teamId/settings', label: 'Settings', leaderOnly: true },
] as const

interface TeamLayoutProps {
  teamId: number
}

export function TeamLayout({ teamId }: TeamLayoutProps) {
  const team = useTeam(teamId)
  const isLeader = team.role === 'leader'

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col px-4 pt-6 sm:px-8">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-heading-3">{team.name}</h1>
        <Badge variant="tag-gray">{isLeader ? 'Leader' : 'Member'}</Badge>
      </div>

      <nav
        aria-label="Team"
        className="mt-3 flex overflow-x-auto border-b [scrollbar-width:none]"
      >
        {TABS.filter((tab) => isLeader || !('leaderOnly' in tab)).map((tab) => (
          <Link
            key={tab.to}
            to={tab.to}
            params={{ teamId }}
            activeOptions={{ exact: 'exact' in tab }}
            className="-mb-px flex h-11 shrink-0 items-center border-b-2 border-transparent px-4 text-body-sm font-medium text-muted-foreground transition-colors duration-150 hover-device:hover:text-foreground data-[status=active]:border-foreground data-[status=active]:text-foreground"
          >
            {tab.label}
          </Link>
        ))}
      </nav>

      <div className="flex flex-col gap-6 py-6">
        <Outlet />
      </div>
    </div>
  )
}
