import { createFileRoute } from '@tanstack/react-router'
import { ChatPage } from '@/features/chat/ChatPage'

export const Route = createFileRoute('/_app/teams/$teamId/chat')({
  head: () => ({ meta: [{ title: 'Team chat | Nesma Airlines' }] }),
  component: ChatRoute,
})

function ChatRoute() {
  const { teamId } = Route.useParams()
  return <ChatPage key={teamId} teamId={teamId} />
}
