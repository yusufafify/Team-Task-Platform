import { Link } from '@tanstack/react-router'
import { Users } from 'lucide-react'
import { Page } from '@/components/shared/Page'
import { EmptyState } from '@/components/shared/States'
import { Button } from '@/components/ui/button'
import { useTeam, useTeams } from '@/features/teams/query'
import { NewTaskDialog } from './TaskFormDialog'
import { TaskBoard } from './TaskBoard'
import type { TaskFilters } from './types'

interface TasksPageProps {
  filters: TaskFilters
  onFiltersChange: (filters: TaskFilters) => void
}

export function TasksPage({ filters, onFiltersChange }: TasksPageProps) {
  const { data: teams } = useTeams()

  return (
    <Page title="Tasks" action={<NewTaskDialog />}>
      {teams?.length === 0 ? (
        <EmptyState
          icon={Users}
          title="Join a team to get started"
          message="Tasks belong to teams. Create one, or ask a team leader to add you by your email."
          action={
            <Button asChild>
              <Link to="/teams">Go to teams</Link>
            </Button>
          }
        />
      ) : (
        <TaskBoard
          filters={filters}
          onFiltersChange={onFiltersChange}
          canCreate={Boolean(teams?.some(({ role }) => role === 'leader'))}
        />
      )}
    </Page>
  )
}

interface TeamTasksPageProps extends TasksPageProps {
  teamId: number
}

export function TeamTasksPage({
  teamId,
  filters,
  onFiltersChange,
}: TeamTasksPageProps) {
  const team = useTeam(teamId)
  const isLeader = team.role === 'leader'

  return (
    <TaskBoard
      filters={filters}
      onFiltersChange={onFiltersChange}
      teamId={teamId}
      canCreate={isLeader}
      action={isLeader && <NewTaskDialog teamId={teamId} />}
    />
  )
}
