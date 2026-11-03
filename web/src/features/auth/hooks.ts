import { useRouter } from '@tanstack/react-router'
import { useSchemaForm } from '@/hooks/useSchemaForm'
import { extractErrorCode } from '@/lib/utils'
import { useLogin, useRegister } from './query'
import { loginSchema, registerSchema } from './schema'
import type { LoginInput } from './types'

const LOGIN_MESSAGES = new Map([
  [
    'no_active_account',
    "That email and password don't match. Check them and try again.",
  ],
  [
    'user_inactive',
    'This account was deactivated. Ask a team leader or an administrator for help.',
  ],
  ['throttled', 'Too many sign-in attempts. Wait a minute, then try again.'],
])

function useSignIn(redirectTo = '/') {
  const login = useLogin()
  const router = useRouter()

  async function signIn(input: LoginInput) {
    try {
      await login.mutateAsync(input)
    } catch (error) {
      const message = LOGIN_MESSAGES.get(extractErrorCode(error) ?? '')
      throw message ? new Error(message) : error
    }
    router.history.push(redirectTo)
  }

  return { signIn, isPending: login.isPending }
}

export function useLoginForm(redirectTo?: string) {
  const { signIn, isPending } = useSignIn(redirectTo)
  const form = useSchemaForm(loginSchema, signIn)
  return { ...form, isPending }
}

export function useRegisterForm() {
  const register = useRegister()
  const { signIn, isPending } = useSignIn()
  const form = useSchemaForm(registerSchema, async (values) => {
    await register.mutateAsync(values)
    await signIn({ email: values.email, password: values.password })
  })
  return { ...form, isPending: register.isPending || isPending }
}
