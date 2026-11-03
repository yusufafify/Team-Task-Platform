import { useState } from 'react'
import { Page } from '@/components/shared/Page'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Field, FormError } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { useSchemaForm } from '@/hooks/useSchemaForm'
import {
  useLogout,
  useLogoutEverywhere,
  useMe,
  useUpdateProfile,
} from './query'
import { profileSchema } from './schema'

export function AccountPage() {
  const user = useMe()
  const update = useUpdateProfile()
  const logout = useLogout()
  const logoutEverywhere = useLogoutEverywhere()
  const [saved, setSaved] = useState(false)
  const { errors, formError, handleSubmit } = useSchemaForm(
    profileSchema,
    async (values) => {
      setSaved(false)
      await update.mutateAsync(values)
      setSaved(true)
    },
  )

  return (
    <Page title="Account">
      <form
        onSubmit={handleSubmit}
        noValidate
        className="flex max-w-lg flex-col gap-5"
      >
        <FormError>{formError}</FormError>
        <Field label="Email" hint="Your email can't be changed.">
          <Input value={user.email} readOnly disabled />
        </Field>
        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="First name" error={errors.first_name}>
            <Input
              name="first_name"
              defaultValue={user.first_name}
              autoComplete="given-name"
            />
          </Field>
          <Field label="Last name" error={errors.last_name}>
            <Input
              name="last_name"
              defaultValue={user.last_name}
              autoComplete="family-name"
            />
          </Field>
        </div>
        <div className="flex items-center gap-3">
          <Button type="submit" disabled={update.isPending}>
            Save changes
          </Button>
          {saved && (
            <p role="status" className="text-body-sm text-success">
              Changes saved
            </p>
          )}
        </div>
      </form>

      <section className="flex max-w-lg flex-col gap-3 border-t pt-6">
        <h2 className="text-heading-5">Sessions</h2>
        <p className="text-body-sm text-muted-foreground">
          Sign out everywhere if a device is lost or you think someone else has
          your account.
        </p>
        <div className="flex flex-wrap gap-3">
          <Button
            variant="outline"
            disabled={logout.isPending}
            onClick={() => logout.mutate()}
          >
            Sign out
          </Button>
          <ConfirmDialog
            trigger={<Button variant="outline">Sign out everywhere</Button>}
            title="Sign out everywhere?"
            message="This ends your sessions on every device, including this one."
            confirmLabel="Sign out everywhere"
            onConfirm={() => logoutEverywhere.mutateAsync()}
          />
        </div>
      </section>
    </Page>
  )
}
