import { createFileRoute } from '@tanstack/react-router'
import { TeamSettingsPage } from '@/features/teams/TeamSettingsPage'

export const Route = createFileRoute('/_app/teams/$teamId/settings')({
  head: () => ({ meta: [{ title: 'Team settings | Nesma Airlines' }] }),
  component: SettingsRoute,
})

function SettingsRoute() {
  const { teamId } = Route.useParams()
  return <TeamSettingsPage key={teamId} teamId={teamId} />
}
