import { createFileRoute } from '@tanstack/react-router'
import { statsSearchSchema } from '@/features/stats/schema'
import { TeamStatsPage } from '@/features/stats/TeamStatsPage'

export const Route = createFileRoute('/_app/teams/$teamId/stats')({
  validateSearch: statsSearchSchema,
  head: () => ({ meta: [{ title: 'Team stats | Nesma Airlines' }] }),
  component: StatsRoute,
})

function StatsRoute() {
  const { teamId } = Route.useParams()
  const period = Route.useSearch()
  const navigate = Route.useNavigate()
  return (
    <TeamStatsPage
      teamId={teamId}
      period={period}
      onPeriodChange={(search) => void navigate({ search })}
    />
  )
}
