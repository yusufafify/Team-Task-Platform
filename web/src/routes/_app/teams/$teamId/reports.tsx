import { createFileRoute } from '@tanstack/react-router'
import { ReportsPage } from '@/features/reports/ReportsPage'

export const Route = createFileRoute('/_app/teams/$teamId/reports')({
  head: () => ({ meta: [{ title: 'Monthly reports | Nesma Airlines' }] }),
  component: ReportsRoute,
})

function ReportsRoute() {
  const { teamId } = Route.useParams()
  return <ReportsPage key={teamId} teamId={teamId} />
}
