import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { http } from '@/lib/http/fetch_instance'
import type { StatsPeriod, TeamStats } from './types'

export function useTeamStats(teamId: number, period: StatsPeriod) {
  return useQuery({
    queryKey: ['stats', teamId, period],
    queryFn: ({ signal }) =>
      http.get<TeamStats>(`teams/${teamId}/stats/`, { params: period, signal }),
    placeholderData: keepPreviousData,
  })
}
