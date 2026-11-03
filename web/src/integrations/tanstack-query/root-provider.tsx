import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query'
import { endExpiredSession } from '@/lib/http/errors'
import { extractStatusCode } from '@/lib/utils'

export function getContext() {
  const queryClient = new QueryClient({
    queryCache: new QueryCache({
      // The route guards answer the "is anyone signed in?" query themselves.
      onError: (error, query) => {
        if (!query.meta?.authCheck) endExpiredSession(error)
      },
    }),
    mutationCache: new MutationCache({ onError: endExpiredSession }),
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
