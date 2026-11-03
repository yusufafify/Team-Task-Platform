import { useSchemaForm } from '@/hooks/use-schema-form';
import { errorCode } from '@/lib/http';

import { register, signIn } from './query';
import { loginSchema, registerSchema } from './schema';
import type { LoginInput } from './types';

const LOGIN_MESSAGES = new Map([
  ['no_active_account', "That email and password don't match. Check them and try again."],
  ['user_inactive', 'This account was deactivated. Ask a team leader or an administrator for help.'],
  ['throttled', 'Too many sign-in attempts. Wait a minute, then try again.'],
]);

async function signInWithMessages(input: LoginInput) {
  try {
    await signIn(input);
  } catch (error) {
    const message = LOGIN_MESSAGES.get(errorCode(error) ?? '');
    throw message ? new Error(message) : error;
  }
}

export function useLoginForm() {
  return useSchemaForm(loginSchema, { email: '', password: '' }, signInWithMessages);
}

export function useRegisterForm() {
  return useSchemaForm(
    registerSchema,
    { first_name: '', last_name: '', email: '', password: '' },
    async (values) => {
      await register(values);
      await signInWithMessages({ email: values.email, password: values.password });
    },
  );
}
