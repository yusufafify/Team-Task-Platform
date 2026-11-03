import { createFileRoute } from '@tanstack/react-router'
import { RegisterPage } from '@/features/auth/RegisterPage'

export const Route = createFileRoute('/_auth/register')({
  head: () => ({ meta: [{ title: 'Create your account | Nesma Airlines' }] }),
  component: RegisterPage,
})
