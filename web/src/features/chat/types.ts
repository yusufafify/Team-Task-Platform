import type { User } from '@/types/api'

export interface Message {
  id: number
  team: number
  author: User
  body: string
  created_at: string
}
