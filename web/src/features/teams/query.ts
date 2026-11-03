import {
  queryOptions,
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
  useSuspenseQuery,
} from '@tanstack/react-query'
import { http } from '@/lib/http/fetch_instance'
import type { Paginated } from '@/types/api'
import type { AddMemberInput, Member, Team, TeamInput, TeamRole } from './types'

const TEAMS_KEY = ['teams']

// The sidebar and every role check need the whole list, so this walks all the pages.
async function fetchAllTeams() {
  const teams: Array<Team> = []
  for (let page = 1; ; page += 1) {
    const { results, next } = await http.get<Paginated<Team>>('teams/', {
      params: { page },
    })
    teams.push(...results)
    if (!next) return teams
  }
}

export const teamsQuery = queryOptions({
  queryKey: TEAMS_KEY,
  queryFn: fetchAllTeams,
  staleTime: 60_000,
})

export const membersQuery = (teamId: number) =>
  queryOptions({
    queryKey: [...TEAMS_KEY, teamId, 'members'],
    queryFn: () => http.get<Array<Member>>(`teams/${teamId}/members/`),
    staleTime: 60_000,
  })

export function useTeams() {
  return useQuery(teamsQuery)
}

// Only for routes under /teams/$teamId, whose loader has checked the team exists.
export function useTeam(teamId: number): Team {
  const { data: teams } = useSuspenseQuery(teamsQuery)
  const team = teams.find(({ id }) => id === teamId)
  // Reached when someone loses the team while its page is open; the route's error screen shows this.
  if (!team) throw new Error('You no longer have access to this team.')
  return team
}

export function useMembers(teamId: number | undefined) {
  return useQuery({
    ...membersQuery(teamId ?? 0),
    enabled: teamId !== undefined,
  })
}

export function useMemberNames(teamIds: ReadonlyArray<number>) {
  return useQueries({
    queries: teamIds.map(membersQuery),
    combine: (results) =>
      new Map(
        results.flatMap(({ data }) =>
          (data ?? []).map(({ user }) => [user.id, user] as const),
        ),
      ),
  })
}

export function useCreateTeam() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: TeamInput) => http.post<Team>('teams/', input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TEAMS_KEY }),
  })
}

export function useUpdateTeam(teamId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: TeamInput) =>
      http.patch<Team>(`teams/${teamId}/`, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TEAMS_KEY }),
  })
}

export function useDeleteTeam(teamId: number) {
  return useMutation({
    mutationFn: () => http.delete<void>(`teams/${teamId}/`),
  })
}

export function useAddMember(teamId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: AddMemberInput) =>
      http.post<Member>(`teams/${teamId}/members/`, input),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: membersQuery(teamId).queryKey,
      }),
  })
}

interface RoleChange {
  userId: number
  role: TeamRole
}

export function useChangeMemberRole(teamId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ userId, role }: RoleChange) =>
      http.patch<Member>(`teams/${teamId}/members/${userId}/`, { role }),
    // The requester's own role can be what changed, and that lives on the team.
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TEAMS_KEY }),
  })
}

export function useRemoveMember(teamId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (userId: number) =>
      http.delete<void>(`teams/${teamId}/members/${userId}/`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TEAMS_KEY })
      // Removing someone unassigns their open tasks.
      return queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}
