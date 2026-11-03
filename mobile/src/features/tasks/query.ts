import {
  keepPreviousData,
  queryOptions,
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';

import { http } from '@/lib/http';
import { nextPage } from '@/lib/pagination';
import type { Paginated } from '@/lib/types';

import type { Comment, NewTaskInput, Task, TaskFilters, TaskFormInput, TaskStatus } from './types';

const TASKS_KEY = ['tasks'];

const taskQuery = (taskId: number) =>
  queryOptions({
    queryKey: [...TASKS_KEY, 'detail', taskId],
    queryFn: ({ signal }) => http.get<Task>(`tasks/${taskId}/`, { signal }),
  });

export function useTasks(filters: TaskFilters) {
  return useInfiniteQuery({
    queryKey: [...TASKS_KEY, 'list', filters],
    queryFn: ({ pageParam, signal }) =>
      http.get<Paginated<Task>>('tasks/', {
        // ?overdue=false means "no filter", so only true is ever sent.
        params: { ...filters, overdue: filters.overdue || undefined, page: pageParam },
        signal,
      }),
    initialPageParam: 1,
    getNextPageParam: nextPage,
    placeholderData: keepPreviousData,
  });
}

export function useTask(taskId: number) {
  return useQuery(taskQuery(taskId));
}

export function useCreateTask() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: NewTaskInput) => http.post<Task>('tasks/', input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: TASKS_KEY }),
  });
}

export function useUpdateTask(taskId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: TaskFormInput | { status: TaskStatus }) => http.patch<Task>(`tasks/${taskId}/`, input),
    onSuccess: (task) => {
      queryClient.setQueryData(taskQuery(taskId).queryKey, task);
      return queryClient.invalidateQueries({ queryKey: TASKS_KEY });
    },
  });
}

export function useDeleteTask(taskId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => http.delete<void>(`tasks/${taskId}/`),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: taskQuery(taskId).queryKey });
      return queryClient.invalidateQueries({ queryKey: TASKS_KEY });
    },
  });
}

export function useComments(taskId: number) {
  return useInfiniteQuery({
    queryKey: ['comments', taskId],
    queryFn: ({ pageParam, signal }) =>
      http.get<Paginated<Comment>>(`tasks/${taskId}/comments/`, { params: { page: pageParam }, signal }),
    initialPageParam: 1,
    getNextPageParam: nextPage,
  });
}

export function useAddComment(taskId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => http.post<Comment>(`tasks/${taskId}/comments/`, { body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['comments', taskId] }),
  });
}
