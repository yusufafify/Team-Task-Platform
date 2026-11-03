import type { Stats } from '@/features/stats/types'

export interface MonthlyReport {
  id: number
  month: string
  stats: Stats
  members: Array<{ name: string; stats: Stats }>
  body: string
  created_at: string
}
