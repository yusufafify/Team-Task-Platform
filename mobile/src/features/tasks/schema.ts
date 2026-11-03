import { z } from 'zod';

export const taskStatusSchema = z.enum(['todo', 'in_progress', 'blocked', 'done']);
export const taskPrioritySchema = z.enum(['low', 'medium', 'high', 'urgent']);

export const taskFormSchema = z.object({
  title: z.string().trim().min(1, 'Give the task a title').max(200),
  description: z.string().max(10_000),
  priority: taskPrioritySchema,
  assignee: z.number().int().nullable(),
  due_at: z.date().transform((date) => date.toISOString()),
});

export const newTaskSchema = taskFormSchema.extend({
  team: z.number().int().positive('Choose a team'),
});
