import { Link } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { Field, FormError } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { useRegisterForm } from './hooks'

export function RegisterPage() {
  const { errors, formError, handleSubmit, isPending } = useRegisterForm()

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-5">
      <h1 className="text-heading-4">Create your account</h1>
      <FormError>{formError}</FormError>
      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="First name" error={errors.first_name}>
          <Input name="first_name" autoComplete="given-name" />
        </Field>
        <Field label="Last name" error={errors.last_name}>
          <Input name="last_name" autoComplete="family-name" />
        </Field>
      </div>
      <Field label="Email" error={errors.email}>
        <Input name="email" type="email" autoComplete="email" required />
      </Field>
      <Field label="Password" error={errors.password}>
        <Input
          name="password"
          type="password"
          autoComplete="new-password"
          required
        />
      </Field>
      <Button type="submit" disabled={isPending}>
        {isPending ? 'Creating your account' : 'Create account'}
      </Button>
      <p className="text-body-sm text-muted-foreground">
        Already have an account?{' '}
        <Link to="/login" className="text-link hover-device:hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  )
}
