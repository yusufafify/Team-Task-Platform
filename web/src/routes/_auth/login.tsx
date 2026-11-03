import { createFileRoute } from '@tanstack/react-router'
import { LoginPage } from '@/features/auth/LoginPage'
import { loginSearchSchema } from '@/features/auth/schema'

export const Route = createFileRoute('/_auth/login')({
  validateSearch: loginSearchSchema,
  head: () => ({ meta: [{ title: 'Sign in | Nesma Airlines' }] }),
  component: LoginRoute,
})

function LoginRoute() {
  const { redirect } = Route.useSearch()
  return <LoginPage redirectTo={redirect} />
}
