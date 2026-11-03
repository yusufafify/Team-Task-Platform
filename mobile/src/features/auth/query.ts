import { queryOptions, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { unregisterPushToken } from '@/features/notifications/push';
import { http, publicPost } from '@/lib/http';
import { clearTokens, getTokens, saveTokens, type Tokens } from '@/lib/session';
import type { User } from '@/lib/types';

import type { LoginInput, ProfileInput, RegisterInput } from './types';

export const meQuery = queryOptions({
  queryKey: ['me'],
  queryFn: ({ signal }) => http.get<User>('auth/me/', { signal }),
  staleTime: Infinity,
});

export function useMe() {
  return useQuery(meQuery);
}

// Saving the tokens flips the session, and the root guard moves to the app.
export async function signIn(input: LoginInput) {
  await saveTokens(await publicPost<Tokens>('auth/mobile/login/', input));
}

export function register(input: RegisterInput) {
  return publicPost<User>('auth/register/', input);
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ProfileInput) => http.patch<User>('auth/me/', input),
    onSuccess: (user) => queryClient.setQueryData(meQuery.queryKey, user),
  });
}

// The overview's order: drop this phone's push token, end the session, then forget the tokens.
// The server calls are best effort, so signing out still works offline.
async function signOut() {
  await unregisterPushToken();
  const refresh = getTokens()?.refresh;
  if (refresh) await publicPost('auth/mobile/logout/', { refresh }).catch(() => undefined);
  await clearTokens();
}

export function useSignOut() {
  return useMutation({ mutationFn: signOut });
}

// The way out of a stolen token, so it fails loudly instead of signing out locally.
export function useSignOutEverywhere() {
  return useMutation({
    mutationFn: async () => {
      await http.post('auth/logout-all/');
      await signOut();
    },
  });
}
