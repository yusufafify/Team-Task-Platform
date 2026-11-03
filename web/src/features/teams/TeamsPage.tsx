import { useState } from 'react'
import { Link, useNavigate } from '@tanstack/react-router'
import { ChevronRight, Users } from 'lucide-react'
import { Page } from '@/components/shared/Page'
import { EmptyState, ErrorState } from '@/components/shared/States'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { FormError } from '@/components/ui/field'
import { Skeleton } from '@/components/ui/skeleton'
import { useSchemaForm } from '@/hooks/useSchemaForm'
import { useCreateTeam, useTeams } from './query'
import { teamSchema } from './schema'
import { TeamFields } from './TeamFields'

function NewTeamDialog() {
  const [open, setOpen] = useState(false)
  const create = useCreateTeam()
  const navigate = useNavigate()
  const { errors, formError, handleSubmit } = useSchemaForm(
    teamSchema,
    async (values) => {
      const team = await create.mutateAsync(values)
      setOpen(false)
      await navigate({
        to: '/teams/$teamId',
        params: { teamId: team.id },
      })
    },
  )

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>New team</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>New team</DialogTitle>
        <DialogDescription>
          You become the team&rsquo;s leader, and can add people by email.
        </DialogDescription>
        <form
          onSubmit={handleSubmit}
          noValidate
          className="flex flex-col gap-5"
        >
          <FormError>{formError}</FormError>
          <TeamFields errors={errors} />
          <Button
            type="submit"
            disabled={create.isPending}
            className="self-end"
          >
            Create team
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function TeamsPage() {
  const { data: teams, error, refetch } = useTeams()

  return (
    <Page title="Teams" action={<NewTeamDialog />}>
      {error ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : !teams ? (
        <div aria-busy="true" className="flex flex-col gap-3">
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
        </div>
      ) : teams.length === 0 ? (
        <EmptyState
          icon={Users}
          title="You're not on a team yet"
          message="Create a team to start assigning work, or ask a team leader to add you by your email."
        />
      ) : (
        <ul className="divide-y rounded-lg border">
          {teams.map((team) => (
            <li key={team.id}>
              <Link
                to="/teams/$teamId"
                params={{ teamId: team.id }}
                className="flex items-center gap-3 px-5 py-4 transition-colors duration-150 hover-device:hover:bg-secondary"
              >
                <span className="min-w-0 flex-1 text-body-md font-medium">
                  {team.name}
                </span>
                <Badge variant="tag-gray">
                  {team.role === 'leader' ? 'Leader' : 'Member'}
                </Badge>
                <ChevronRight
                  className="size-4 text-muted-foreground"
                  aria-hidden="true"
                />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Page>
  )
}
