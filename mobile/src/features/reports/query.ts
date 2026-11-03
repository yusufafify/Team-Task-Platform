import { useInfiniteQuery } from '@tanstack/react-query';

import { http } from '@/lib/http';
import { nextPage } from '@/lib/pagination';
import type { Paginated } from '@/lib/types';

import type { MonthlyReport } from './types';

// Leaders only: a member gets 403, so callers pass `enabled` from the team's role.
export function useReports(teamId: number, enabled: boolean) {
  return useInfiniteQuery({
    queryKey: ['reports', teamId],
    queryFn: ({ pageParam, signal }) =>
      http.get<Paginated<MonthlyReport>>(`teams/${teamId}/reports/`, { params: { page: pageParam }, signal }),
    initialPageParam: 1,
    getNextPageParam: nextPage,
    enabled,
  });
}
