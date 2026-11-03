import {
  infiniteQueryOptions,
  keepPreviousData,
  queryOptions,
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { http } from '@/lib/http/fetch_instance'
import type { Paginated } from '@/types/api'
import type {
  Comment,
  NewTaskInput,
  Task,
  TaskFilters,
  TaskFormInput,
  TaskStatus,
} from './types'

export const TASK_PAGE_SIZE = 20

const TASKS_KEY = ['tasks']

const tasksQuery = (filters: TaskFilters) =>
  queryOptions({
    queryKey: [...TASKS_KEY, 'list', filters],
    queryFn: ({ signal }) =>
      http.get<Paginated<Task>>('tasks/', {
        // ?overdue=false means "no filter", so only true is ever sent.
        params: { ...filters, overdue: filters.overdue || undefined },
        signal,
      }),
    placeholderData: keepPreviousData,
  })

const taskQuery = (taskId: number) =>
  queryOptions({
    queryKey: [...TASKS_KEY, 'detail', taskId],
    queryFn: ({ signal }) => http.get<Task>(`tasks/${taskId}/`, { signal }),
  })

const commentsQuery = (taskId: number) =>
  infiniteQueryOptions({
    queryKey: ['comments', taskId],
    queryFn: ({ pageParam, signal }) =>
      http.get<Paginated<Comment>>(`tasks/${taskId}/comments/`, {
        params: { page: pageParam },
        signal,
      }),
    initialPageParam: 1,
    getNextPageParam: (last, _pages, page) =>
      last.next ? page + 1 : undefined,
  })

export function useTasks(filters: TaskFilters) {
  return useQuery(tasksQuery(filters))
}

export function useTask(taskId: number) {
  return useQuery(taskQuery(taskId))
}

export function useCreateTask() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: NewTaskInput) => http.post<Task>('tasks/', input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TASKS_KEY }),
  })
}

export function useUpdateTask(taskId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: TaskFormInput | { status: TaskStatus }) =>
      http.patch<Task>(`tasks/${taskId}/`, input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TASKS_KEY }),
  })
}

export function useDeleteTask(taskId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => http.delete<void>(`tasks/${taskId}/`),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: taskQuery(taskId).queryKey })
      return queryClient.invalidateQueries({ queryKey: TASKS_KEY })
    },
  })
}

export function useComments(taskId: number) {
  return useInfiniteQuery(commentsQuery(taskId))
}

export function useAddComment(taskId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: string) =>
      http.post<Comment>(`tasks/${taskId}/comments/`, { body }),
    onSuccess: () =>
      queryClient.invalidateQueries({
        queryKey: commentsQuery(taskId).queryKey,
      }),
  })
}
