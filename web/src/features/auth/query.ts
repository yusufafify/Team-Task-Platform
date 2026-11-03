import {
  queryOptions,
  useMutation,
  useQueryClient,
  useSuspenseQuery,
} from '@tanstack/react-query'
import { http } from '@/lib/http/fetch_instance'
import type { User } from '@/types/api'
import type { LoginInput, ProfileInput, RegisterInput } from './types'

export const meQuery = queryOptions({
  queryKey: ['me'],
  queryFn: () => http.get<User>('auth/me/'),
  staleTime: Infinity,
  meta: { authCheck: true },
})

// Only rendered under the /_app guard, which has already loaded this.
export function useMe() {
  return useSuspenseQuery(meQuery).data
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: LoginInput) => http.post<User>('auth/login/', input),
    onSuccess: (user) => queryClient.setQueryData(meQuery.queryKey, user),
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: (input: RegisterInput) =>
      http.post<User>('auth/register/', input),
  })
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: ProfileInput) => http.patch<User>('auth/me/', input),
    onSuccess: (user) => queryClient.setQueryData(meQuery.queryKey, user),
  })
}

// Both end in a full page load, which also drops everything cached for this person.
function leaveApp() {
  window.location.assign('/login')
}

export function useLogout() {
  return useMutation({
    mutationFn: () => http.post<void>('auth/logout/'),
    onSuccess: leaveApp,
  })
}

export function useLogoutEverywhere() {
  return useMutation({
    // An access token outlives logout-all by up to 15 minutes, and only logout clears the cookies.
    mutationFn: async () => {
      await http.post<void>('auth/logout-all/')
      await http.post<void>('auth/logout/')
    },
    onSuccess: leaveApp,
  })
}
