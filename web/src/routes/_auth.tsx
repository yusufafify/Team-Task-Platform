import { createFileRoute, redirect } from '@tanstack/react-router'
import { AuthLayout } from '@/features/auth/AuthLayout'
import { meQuery } from '@/features/auth/query'

export const Route = createFileRoute('/_auth')({
  beforeLoad: async ({ context }) => {
    const user = await context.queryClient
      .ensureQueryData(meQuery)
      .catch(() => null)
    if (user) throw redirect({ to: '/' })
  },
  component: AuthLayout,
})
