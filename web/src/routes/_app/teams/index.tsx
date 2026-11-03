import { createFileRoute } from '@tanstack/react-router'
import { TeamsPage } from '@/features/teams/TeamsPage'

export const Route = createFileRoute('/_app/teams/')({
  head: () => ({ meta: [{ title: 'Teams | Nesma Airlines' }] }),
  component: TeamsPage,
})
