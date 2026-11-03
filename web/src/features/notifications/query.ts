import {
  infiniteQueryOptions,
  queryOptions,
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { http } from '@/lib/http/fetch_instance'
import type { Paginated } from '@/types/api'
import type { Notification } from './types'

export const NOTIFICATIONS_KEY = ['notifications']

export const unreadCountQuery = queryOptions({
  queryKey: [...NOTIFICATIONS_KEY, 'unread'],
  queryFn: ({ signal }) =>
    http.get<Paginated<Notification>>('notifications/', {
      params: { unread: true },
      signal,
    }),
  select: (data) => data.count,
  // New ones arrive on the socket. This is the required check on focus; there is no timer.
  refetchOnWindowFocus: true,
})

const notificationsQuery = infiniteQueryOptions({
  queryKey: [...NOTIFICATIONS_KEY, 'list'],
  queryFn: ({ pageParam, signal }) =>
    http.get<Paginated<Notification>>('notifications/', {
      params: { page: pageParam },
      signal,
    }),
  initialPageParam: 1,
  getNextPageParam: (last, _pages, page) => (last.next ? page + 1 : undefined),
})

export function useUnreadCount() {
  return useQuery(unreadCountQuery)
}

export function useNotifications() {
  return useInfiniteQuery(notificationsQuery)
}

export function useMarkRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) =>
      http.post<Notification>(`notifications/${id}/read/`),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_KEY }),
  })
}

export function useMarkAllRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => http.post<void>('notifications/read-all/'),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_KEY }),
  })
}
