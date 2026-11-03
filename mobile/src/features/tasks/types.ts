import type { z } from 'zod';

import type { User } from '@/lib/types';

import type { newTaskSchema, taskFormSchema, taskPrioritySchema, taskStatusSchema } from './schema';

export type TaskStatus = z.infer<typeof taskStatusSchema>;
export type TaskPriority = z.infer<typeof taskPrioritySchema>;
export type TaskFormInput = z.output<typeof taskFormSchema>;
export type NewTaskInput = z.output<typeof newTaskSchema>;

export interface TaskFilters {
  team?: number;
  status?: TaskStatus;
  overdue?: boolean;
}

export interface Task {
  id: number;
  team: number;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  assignee: number | null;
  created_by: number;
  due_at: string;
  completed_at: string | null;
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: number;
  task: number;
  author: User;
  body: string;
  created_at: string;
}
