import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { Field, FormError } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { useLoginForm } from './hooks'

interface LoginPageProps {
  redirectTo?: string
}

export function LoginPage({ redirectTo }: LoginPageProps) {
  const { errors, formError, handleSubmit, isPending } =
    useLoginForm(redirectTo)

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
      <h1 className="text-heading-4">Sign in</h1>
      <FormError>{formError}</FormError>
      <Field label="Email" error={errors.email}>
        <Input name="email" type="email" autoComplete="email" required />
      </Field>
      <Field label="Password" error={errors.password}>
        <Input
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </Field>
      <Button type="submit" disabled={isPending}>
        {isPending ? 'Signing in' : 'Sign in'}
      </Button>
      <p className="text-body-sm text-muted-foreground">
        New here?{' '}
        <Link to="/register" className="text-link hover-device:hover:underline">
          Create an account
        </Link>
      </p>
    </form>
  )
}
