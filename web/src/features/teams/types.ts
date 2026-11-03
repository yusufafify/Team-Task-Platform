import type { z } from 'zod'
import type { User } from '@/types/api'
import type { addMemberSchema, teamRoleSchema, teamSchema } from './schema'

export type TeamRole = z.infer<typeof teamRoleSchema>
export type TeamInput = z.infer<typeof teamSchema>
export type AddMemberInput = z.infer<typeof addMemberSchema>

export interface Team {
  id: number
  name: string
  timezone?: string
  role: TeamRole
  created_at: string
}

export interface Member {
  user: User
  role: TeamRole
  joined_at: string
}
