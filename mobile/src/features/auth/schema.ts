import { z } from 'zod';

const email = z.string().trim().pipe(z.email('Enter a valid email address').max(254));

export const loginSchema = z.object({
  email,
  password: z.string().min(1, 'Enter your password'),
});

export const registerSchema = z.object({
  first_name: z.string().trim().max(150),
  last_name: z.string().trim().max(150),
  email,
  password: z.string().min(1, 'Choose a password').max(128),
});

export const profileSchema = registerSchema.pick({ first_name: true, last_name: true });
