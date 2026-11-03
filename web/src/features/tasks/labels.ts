import type { TaskPriority, TaskStatus } from './types'

export const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'To do',
  in_progress: 'In progress',
  blocked: 'Blocked',
  done: 'Done',
}

export const PRIORITY_LABELS: Record<TaskPriority, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  urgent: 'Urgent',
}

export const PRIORITY_BADGES = {
  low: 'tag-gray',
  medium: 'tag-purple',
  high: 'tag-orange',
  urgent: 'orange',
} as const
