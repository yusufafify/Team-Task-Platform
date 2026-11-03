import { createFileRoute } from '@tanstack/react-router'
import { AccountPage } from '@/features/auth/AccountPage'

export const Route = createFileRoute('/_app/account')({
  head: () => ({ meta: [{ title: 'Account | Nesma Airlines' }] }),
  component: AccountPage,
})
