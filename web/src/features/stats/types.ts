import type { z } from 'zod'
import type { User } from '@/types/api'
import type { statsSearchSchema } from './schema'

export type StatsPeriod = z.infer<typeof statsSearchSchema>

export interface Stats {
  due: number
  completed: number
  on_time: number
  delayed: number
  overdue: number
  completion_rate: number | null
  on_time_rate: number | null
  average_delay_days: number | null
}

export interface TeamStats {
  start: string
  end: string
  timezone: string
  scope: 'team' | 'self'
  stats: Stats
  members: Array<{ user: User; stats: Stats }>
}
