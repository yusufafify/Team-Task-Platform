import { createFileRoute } from '@tanstack/react-router'
import { TaskPage } from '@/features/tasks/TaskPage'

export const Route = createFileRoute('/_app/tasks/$taskId')({
  params: {
    parse: ({ taskId }) => ({ taskId: Number(taskId) }),
    stringify: ({ taskId }) => ({ taskId: String(taskId) }),
  },
  head: () => ({ meta: [{ title: 'Task | Nesma Airlines' }] }),
  component: TaskRoute,
})

function TaskRoute() {
  const { taskId } = Route.useParams()
  return <TaskPage taskId={taskId} />
}
