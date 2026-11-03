import type { z } from 'zod'
import type { User } from '@/types/api'
import type {
  newTaskSchema,
  taskFiltersSchema,
  taskFormSchema,
  taskPrioritySchema,
  taskStatusSchema,
} from './schema'

export type TaskStatus = z.infer<typeof taskStatusSchema>
export type TaskPriority = z.infer<typeof taskPrioritySchema>
export type TaskFilters = z.infer<typeof taskFiltersSchema>
export type TaskFormInput = z.infer<typeof taskFormSchema>
export type NewTaskInput = z.infer<typeof newTaskSchema>

export interface Task {
  id: number
  team: number
  title: string
  description?: string
  status: TaskStatus
  priority: TaskPriority
  assignee: number | null
  created_by: number
  due_at: string
  completed_at: string | null
  is_overdue: boolean
  created_at: string
  updated_at: string
}

export interface Comment {
  id: number
  task: number
  author: User
  body: string
  created_at: string
}
