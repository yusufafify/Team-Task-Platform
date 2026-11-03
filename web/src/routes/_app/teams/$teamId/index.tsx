import { createFileRoute } from '@tanstack/react-router'
import { taskFiltersSchema } from '@/features/tasks/schema'
import { TeamTasksPage } from '@/features/tasks/TasksPage'

export const Route = createFileRoute('/_app/teams/$teamId/')({
  validateSearch: taskFiltersSchema,
  head: () => ({ meta: [{ title: 'Team tasks | Nesma Airlines' }] }),
  component: TeamTasksRoute,
})

function TeamTasksRoute() {
  const { teamId } = Route.useParams()
  const filters = Route.useSearch()
  const navigate = Route.useNavigate()
  return (
    <TeamTasksPage
      teamId={teamId}
      filters={filters}
      onFiltersChange={(search) => void navigate({ search })}
    />
  )
}
