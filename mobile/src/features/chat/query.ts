import {
  infiniteQueryOptions,
  useInfiniteQuery,
  useMutation,
  useQueryClient,
  type QueryClient,
} from '@tanstack/react-query';

import { http } from '@/lib/http';
import { applyLatestPage, mergeIntoFirstPage, nextCursor } from '@/lib/pagination';
import type { CursorPage } from '@/lib/types';

import type { Message } from './types';

const CHAT_KEY = 'chat';

function fetchMessages(teamId: number, cursor?: string | null, signal?: AbortSignal) {
  return http.get<CursorPage<Message>>(`teams/${teamId}/messages/`, {
    params: { cursor: cursor ?? undefined },
    signal,
  });
}

const chatQuery = (teamId: number) =>
  infiniteQueryOptions({
    queryKey: [CHAT_KEY, teamId],
    queryFn: ({ pageParam, signal }) => fetchMessages(teamId, pageParam, signal),
    initialPageParam: null as string | null,
    getNextPageParam: nextCursor,
  });

export function useMessages(teamId: number) {
  return useInfiniteQuery(chatQuery(teamId));
}

export function addMessage(client: QueryClient, message: Message) {
  client.setQueryData(chatQuery(message.team).queryKey, (old) => old && mergeIntoFirstPage(old, [message]));
}

export function useSendMessage(teamId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => http.post<Message>(`teams/${teamId}/messages/`, { body }),
    onSuccess: (message) => addMessage(queryClient, message),
  });
}

// The socket can miss events, so REST is the record. Only an open chat is fetched.
export async function syncOpenChats(client: QueryClient) {
  const open = client.getQueryCache().findAll({ queryKey: [CHAT_KEY], type: 'active' });
  await Promise.allSettled(
    open.map(async ({ queryKey }) => {
      const teamId = Number(queryKey[1]);
      const latest = await fetchMessages(teamId);
      client.setQueryData(chatQuery(teamId).queryKey, (old) => old && applyLatestPage(old, latest));
    }),
  );
}
