import { z } from 'zod'

export const taskStatusSchema = z.enum([
  'todo',
  'in_progress',
  'blocked',
  'done',
])
export const taskPrioritySchema = z.enum(['low', 'medium', 'high', 'urgent'])

export const taskFiltersSchema = z.object({
  status: taskStatusSchema.optional().catch(undefined),
  priority: taskPrioritySchema.optional().catch(undefined),
  team: z.number().int().optional().catch(undefined),
  assignee: z.number().int().optional().catch(undefined),
  overdue: z.boolean().optional().catch(undefined),
  page: z.number().int().min(1).optional().catch(undefined),
})

export const taskFormSchema = z.object({
  title: z.string().trim().min(1, 'Give the task a title').max(200),
  description: z.string().max(10_000),
  priority: taskPrioritySchema,
  assignee: z.preprocess(
    (value) => (value === '' ? null : Number(value)),
    z.number().int().nullable(),
  ),
  due_at: z
    .string()
    .min(1, 'Choose when this is due')
    .transform((value) => new Date(value).toISOString()),
})

export const newTaskSchema = taskFormSchema.extend({
  team: z.coerce.number().int().positive('Choose a team'),
})

export const commentSchema = z.object({
  body: z.string().trim().min(1, 'Write a comment first').max(5000),
})
