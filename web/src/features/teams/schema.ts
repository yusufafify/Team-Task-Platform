import { z } from 'zod'

export const teamRoleSchema = z.enum(['leader', 'member'])

export const teamSchema = z.object({
  name: z.string().trim().min(1, 'Give the team a name').max(150),
  timezone: z.string().min(1).max(64),
})

export const addMemberSchema = z.object({
  email: z.email('Enter a valid email address'),
  role: teamRoleSchema,
})
