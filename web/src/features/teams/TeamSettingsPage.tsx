import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useQueryClient } from '@tanstack/react-query'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { FormError } from '@/components/ui/field'
import { useSchemaForm } from '@/hooks/useSchemaForm'
import { LeadersOnly } from './LeadersOnly'
import { teamsQuery, useDeleteTeam, useTeam, useUpdateTeam } from './query'
import { teamSchema } from './schema'
import { TeamFields } from './TeamFields'

interface TeamSettingsPageProps {
  teamId: number
}

export function TeamSettingsPage({ teamId }: TeamSettingsPageProps) {
  const team = useTeam(teamId)
  const update = useUpdateTeam(teamId)
  const remove = useDeleteTeam(teamId)
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [saved, setSaved] = useState(false)
  const { errors, formError, handleSubmit } = useSchemaForm(
    teamSchema,
    async (values) => {
      setSaved(false)
      await update.mutateAsync(values)
      setSaved(true)
    },
  )

  if (team.role !== 'leader') {
    return <LeadersOnly title="Team settings" />
  }

  async function deleteTeam() {
    await remove.mutateAsync()
    await navigate({ to: '/teams' })
    await queryClient.invalidateQueries({ queryKey: teamsQuery.queryKey })
  }

  return (
    <>
      <form
        onSubmit={handleSubmit}
        noValidate
        className="flex max-w-lg flex-col gap-5"
      >
        <FormError>{formError}</FormError>
        <TeamFields team={team} errors={errors} />
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

      <section className="flex max-w-lg flex-col items-start gap-3 border-t pt-6">
        <h2 className="text-heading-5">Delete this team</h2>
        <p className="text-body-sm text-muted-foreground">
          Only a team with no tasks or messages can be deleted.
        </p>
        <ConfirmDialog
          trigger={<Button variant="outline">Delete team</Button>}
          title={`Delete ${team.name}?`}
          message="This can't be undone."
          confirmLabel="Delete team"
          onConfirm={deleteTeam}
        />
      </section>
    </>
  )
}
