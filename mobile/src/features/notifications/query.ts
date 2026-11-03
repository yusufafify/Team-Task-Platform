import { queryOptions, useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { http } from '@/lib/http';
import { nextPage } from '@/lib/pagination';
import type { Paginated } from '@/lib/types';

import type { Notification } from './types';

export const NOTIFICATIONS_KEY = ['notifications'];

// The badge. New ones arrive on the socket; this is the check on open, focus and screen
// change, with no timer of its own.
export const unreadCountQuery = queryOptions({
  queryKey: [...NOTIFICATIONS_KEY, 'unread'],
  queryFn: ({ signal }) => http.get<Paginated<Notification>>('notifications/', { params: { unread: true }, signal }),
  select: (data) => data.count,
});

export function useUnreadCount() {
  return useQuery(unreadCountQuery);
}

export function useNotifications() {
  return useInfiniteQuery({
    queryKey: [...NOTIFICATIONS_KEY, 'list'],
    queryFn: ({ pageParam, signal }) =>
      http.get<Paginated<Notification>>('notifications/', { params: { page: pageParam }, signal }),
    initialPageParam: 1,
    getNextPageParam: nextPage,
  });
}

export function markRead(id: number) {
  return http.post<Notification>(`notifications/${id}/read/`);
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => http.post<void>('notifications/read-all/'),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_KEY }),
  });
}
