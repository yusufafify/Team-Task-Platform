import { QueryClient } from '@tanstack/react-query'
import { extractStatusCode } from '@/lib/utils'

export function getContext() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        refetchOnWindowFocus: false,
        // Only server (5xx) and network failures are worth retrying; a 4xx will fail the same way again.
        retry: (failureCount, error) =>
          failureCount < 2 && extractStatusCode(error) >= 500,
      },
    },
  })

  return {
    queryClient,
  }
}
