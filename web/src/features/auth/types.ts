import type { z } from 'zod'
import type { loginSchema, profileSchema, registerSchema } from './schema'

export type LoginInput = z.infer<typeof loginSchema>
export type RegisterInput = z.infer<typeof registerSchema>
export type ProfileInput = z.infer<typeof profileSchema>
