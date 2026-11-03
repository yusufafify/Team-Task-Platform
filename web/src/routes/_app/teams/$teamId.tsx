import { createFileRoute, notFound } from '@tanstack/react-router'
import { teamsQuery } from '@/features/teams/query'
import { TeamLayout } from '@/features/teams/TeamLayout'
import type { Team } from '@/features/teams/types'

export const Route = createFileRoute('/_app/teams/$teamId')({
  params: {
    parse: ({ teamId }) => ({ teamId: Number(teamId) }),
    stringify: ({ teamId }) => ({ teamId: String(teamId) }),
  },
  // notFound() belongs here: a route needs its own notFoundComponent to catch one thrown in render.
  loader: async ({ context: { queryClient }, params: { teamId } }) => {
    const hasTeam = (teams: Array<Team>) =>
      teams.some(({ id }) => id === teamId)

    const cached = await queryClient.ensureQueryData(teamsQuery)
    if (hasTeam(cached)) return
    // Leaders add people directly, so the cached list can simply be behind.
    const fresh = await queryClient.fetchQuery({ ...teamsQuery, staleTime: 0 })
    if (!hasTeam(fresh)) throw notFound()
  },
  component: TeamRoute,
})

function TeamRoute() {
  const { teamId } = Route.useParams()
  return <TeamLayout teamId={teamId} />
}
