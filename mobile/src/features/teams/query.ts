import { queryOptions, useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query';

import { http } from '@/lib/http';
import type { Paginated } from '@/lib/types';

import type { AddMemberInput, Member, Team, TeamInput, TeamRole } from './types';

const TEAMS_KEY = ['teams'];

// Every role check and team picker needs the whole list, so this walks all the pages.
async function fetchAllTeams() {
  const teams: Team[] = [];
  for (let page = 1; ; page += 1) {
    const { results, next } = await http.get<Paginated<Team>>('teams/', { params: { page } });
    teams.push(...results);
    if (!next) return teams;
  }
}

export const teamsQuery = queryOptions({
  queryKey: TEAMS_KEY,
  queryFn: fetchAllTeams,
  staleTime: 60_000,
});

const membersQuery = (teamId: number) =>
  queryOptions({
    queryKey: [...TEAMS_KEY, teamId, 'members'],
    queryFn: ({ signal }) => http.get<Member[]>(`teams/${teamId}/members/`, { signal }),
    staleTime: 60_000,
  });

export function useTeams() {
  return useQuery(teamsQuery);
}

export function useTeam(teamId: number) {
  const query = useTeams();
  return { ...query, team: query.data?.find(({ id }) => id === teamId) };
}

export function useMembers(teamId: number | undefined) {
  return useQuery({ ...membersQuery(teamId ?? 0), enabled: teamId !== undefined });
}

export function useMemberNames(teamIds: readonly number[]) {
  return useQueries({
    queries: teamIds.map(membersQuery),
    combine: (results) =>
      new Map(results.flatMap(({ data }) => (data ?? []).map(({ user }) => [user.id, user] as const))),
  });
}

export function useCreateTeam() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: TeamInput) => http.post<Team>('teams/', input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TEAMS_KEY }),
  });
}

export function useUpdateTeam(teamId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: TeamInput) => http.patch<Team>(`teams/${teamId}/`, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TEAMS_KEY }),
  });
}

export function useDeleteTeam(teamId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => http.delete<void>(`teams/${teamId}/`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TEAMS_KEY }),
  });
}

export function useAddMember(teamId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: AddMemberInput) => http.post<Member>(`teams/${teamId}/members/`, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: membersQuery(teamId).queryKey }),
  });
}

export function useChangeMemberRole(teamId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: TeamRole }) =>
      http.patch<Member>(`teams/${teamId}/members/${userId}/`, { role }),
    // The requester's own role can be what changed, and that lives on the team.
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TEAMS_KEY }),
  });
}

export function useRemoveMember(teamId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: number) => http.delete<void>(`teams/${teamId}/members/${userId}/`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: TEAMS_KEY });
      // Removing someone unassigns their open tasks.
      return queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}
