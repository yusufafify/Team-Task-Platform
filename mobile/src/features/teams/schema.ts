import { z } from 'zod';

export const teamRoleSchema = z.enum(['leader', 'member']);

export const teamSchema = z.object({
  name: z.string().trim().min(1, 'Give the team a name').max(150),
  timezone: z.string().trim().min(1, 'Enter a timezone, such as Africa/Cairo').max(64),
});

export const addMemberSchema = z.object({
  email: z.string().trim().pipe(z.email('Enter a valid email address')),
  role: teamRoleSchema,
});
