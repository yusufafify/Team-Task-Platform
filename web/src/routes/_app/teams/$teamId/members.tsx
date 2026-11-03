import { createFileRoute } from '@tanstack/react-router'
import { MembersPage } from '@/features/teams/MembersPage'

export const Route = createFileRoute('/_app/teams/$teamId/members')({
  head: () => ({ meta: [{ title: 'Team members | Nesma Airlines' }] }),
  component: MembersRoute,
})

function MembersRoute() {
  const { teamId } = Route.useParams()
  return <MembersPage teamId={teamId} />
}
