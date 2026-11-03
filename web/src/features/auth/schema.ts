import { z } from 'zod'

export const loginSchema = z.object({
  email: z.email('Enter a valid email address'),
  password: z.string().min(1, 'Enter your password'),
})

export const registerSchema = z.object({
  first_name: z.string().trim().max(150),
  last_name: z.string().trim().max(150),
  email: z.email('Enter a valid email address').max(254),
  password: z.string().min(1, 'Choose a password').max(128),
})

export const profileSchema = registerSchema.pick({
  first_name: true,
  last_name: true,
})

// Same-origin paths only, so a crafted link can't send someone off-site after they sign in.
export const loginSearchSchema = z.object({
  redirect: z
    .string()
    .regex(/^\/(?![/\\])/)
    .optional()
    .catch(undefined),
})
