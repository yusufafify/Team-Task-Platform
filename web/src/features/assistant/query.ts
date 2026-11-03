import {
  infiniteQueryOptions,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query'
import { http } from '@/lib/http/fetch_instance'
import { mergeIntoFirstPage, nextCursor } from '@/lib/pagination'
import type { CursorPage } from '@/types/api'
import type { AssistantMessage, AssistantTurn } from './types'

const threadQuery = (teamId: number) =>
  infiniteQueryOptions({
    queryKey: ['assistant', teamId],
    queryFn: ({ pageParam, signal }) =>
      http.get<CursorPage<AssistantMessage>>(
        `teams/${teamId}/assistant/messages/`,
        { params: { cursor: pageParam ?? undefined }, signal },
      ),
    initialPageParam: null as string | null,
    getNextPageParam: nextCursor,
    // Only its owner changes a thread, so it never needs a refetch or a poll.
    staleTime: Infinity,
  })

export function useAssistantThread(teamId: number) {
  return useInfiniteQuery(threadQuery(teamId))
}

// Writes have no timeout in the facade, which leaves room for the 25 seconds an answer can take,
// and mutations don't retry, which matters here because each try spends scarce AI requests.
export function useAskAssistant(teamId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (question: string) =>
      http.post<AssistantTurn>(`teams/${teamId}/assistant/messages/`, {
        question,
      }),
    onSuccess: ({ question, answer }) =>
      queryClient.setQueryData(
        threadQuery(teamId).queryKey,
        (old) => old && mergeIntoFirstPage(old, [question, answer]),
      ),
  })
}

export function useClearThread(teamId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => http.delete<void>(`teams/${teamId}/assistant/messages/`),
    onSuccess: () =>
      queryClient.resetQueries({ queryKey: threadQuery(teamId).queryKey }),
  })
}
