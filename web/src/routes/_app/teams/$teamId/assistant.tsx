import { createFileRoute } from '@tanstack/react-router'
import { AssistantPage } from '@/features/assistant/AssistantPage'

export const Route = createFileRoute('/_app/teams/$teamId/assistant')({
  head: () => ({ meta: [{ title: 'Assistant | Nesma Airlines' }] }),
  component: AssistantRoute,
})

function AssistantRoute() {
  const { teamId } = Route.useParams()
  return <AssistantPage key={teamId} teamId={teamId} />
}
