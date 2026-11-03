import { createFileRoute, redirect } from '@tanstack/react-router'
import { meQuery } from '@/features/auth/query'
import { AppShell } from '@/features/shell/AppShell'
import { extractStatusCode } from '@/lib/utils'

export const Route = createFileRoute('/_app')({
  beforeLoad: async ({ context, location }) => {
    try {
      await context.queryClient.ensureQueryData(meQuery)
    } catch (error) {
      if (extractStatusCode(error) !== 401) throw error
      throw redirect({ to: '/login', search: { redirect: location.href } })
    }
  },
  component: AppShell,
})
