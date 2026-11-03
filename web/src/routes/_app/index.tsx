import { createFileRoute } from '@tanstack/react-router'
import { taskFiltersSchema } from '@/features/tasks/schema'
import { TasksPage } from '@/features/tasks/TasksPage'

export const Route = createFileRoute('/_app/')({
  validateSearch: taskFiltersSchema,
  head: () => ({ meta: [{ title: 'Tasks | Nesma Airlines' }] }),
  component: TasksRoute,
})

function TasksRoute() {
  const filters = Route.useSearch()
  const navigate = Route.useNavigate()
  return (
    <TasksPage
      filters={filters}
      onFiltersChange={(search) => void navigate({ search })}
    />
  )
}
