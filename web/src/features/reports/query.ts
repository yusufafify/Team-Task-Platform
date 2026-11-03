import { useInfiniteQuery } from '@tanstack/react-query'
import { http } from '@/lib/http/fetch_instance'
import type { Paginated } from '@/types/api'
import type { MonthlyReport } from './types'

export function useReports(teamId: number, enabled: boolean) {
  return useInfiniteQuery({
    queryKey: ['reports', teamId],
    queryFn: ({ pageParam, signal }) =>
      http.get<Paginated<MonthlyReport>>(`teams/${teamId}/reports/`, {
        params: { page: pageParam },
        signal,
      }),
    initialPageParam: 1,
    getNextPageParam: (last, _pages, page) =>
      last.next ? page + 1 : undefined,
    enabled,
  })
}
