import { Link } from '@tanstack/react-router'
import { AlertTriangle, ListChecks } from 'lucide-react'
import type { ReactNode } from 'react'
import { EmptyState, ErrorState } from '@/components/shared/States'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useMe } from '@/features/auth/query'
import { useMemberNames, useTeams } from '@/features/teams/query'
import { displayName, formatDayTime } from '@/lib/format'
import { cn } from '@/lib/utils'
import type { User } from '@/types/api'
import { PRIORITY_BADGES, PRIORITY_LABELS, STATUS_LABELS } from './labels'
import { TASK_PAGE_SIZE, useTasks } from './query'
import { taskPrioritySchema, taskStatusSchema } from './schema'
import { StatusSelect } from './StatusSelect'
import type { Task, TaskFilters } from './types'

// The board reads like a departures board: due time first, in the API's earliest-due order.
const ROW =
  'grid gap-x-4 gap-y-2 @3xl:grid-cols-[136px_minmax(0,1fr)_140px_80px_140px] @3xl:items-center'

const FILTER_PILL =
  'h-11 shrink-0 rounded-full border px-4 text-body-sm font-medium text-muted-foreground transition-colors duration-150 hover-device:hover:text-foreground aria-pressed:border-inverse aria-pressed:bg-inverse aria-pressed:text-inverse-foreground lg:h-9'

interface TaskRowProps {
  task: Task
  assignee?: User
  teamName?: string
}

function TaskRow({ task, assignee, teamName }: TaskRowProps) {
  return (
    <li className={cn(ROW, 'px-4 py-3')}>
      <div className="flex flex-wrap items-center gap-x-2 @3xl:flex-col @3xl:items-start">
        <span className="text-body-sm font-semibold tabular-nums">
          {formatDayTime(task.due_at)}
        </span>
        {task.is_overdue && (
          <span className="inline-flex items-center gap-1 text-caption text-destructive-text">
            <AlertTriangle className="size-3" aria-hidden="true" />
            Overdue
          </span>
        )}
      </div>
      <div className="min-w-0">
        <Link
          to="/tasks/$taskId"
          params={{ taskId: task.id }}
          className="-my-1.5 block py-1.5 text-body-sm font-medium hover-device:hover:underline"
        >
          {task.title}
        </Link>
        {teamName && (
          <p className="text-caption text-muted-foreground">{teamName}</p>
        )}
      </div>
      <p className="text-body-sm text-muted-foreground">
        <span className="sr-only">Assigned to </span>
        {assignee ? displayName(assignee) : 'Unassigned'}
      </p>
      <div>
        <Badge variant={PRIORITY_BADGES[task.priority]}>
          <span className="sr-only">Priority </span>
          {PRIORITY_LABELS[task.priority]}
        </Badge>
      </div>
      <StatusSelect task={task} />
    </li>
  )
}

function BoardSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading tasks" className="divide-y">
      {[0, 1, 2, 3].map((row) => (
        <div key={row} className={cn(ROW, 'px-4 py-3')}>
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-5 w-3/4" />
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-5 w-14" />
          <Skeleton className="h-9" />
        </div>
      ))}
    </div>
  )
}

interface TaskBoardProps {
  filters: TaskFilters
  onFiltersChange: (filters: TaskFilters) => void
  // Set on a team's page: fixes the team and offers its roster as a filter.
  teamId?: number
  canCreate: boolean
  action?: ReactNode
}

export function TaskBoard({
  filters,
  onFiltersChange,
  teamId,
  canCreate,
  action,
}: TaskBoardProps) {
  const me = useMe()
  const { data: teams = [] } = useTeams()
  const scopedFilters = teamId ? { ...filters, team: teamId } : filters
  const { data, error, refetch, isPlaceholderData } = useTasks(scopedFilters)
  const shownTeams = teamId ? [teamId] : teams.map(({ id }) => id)
  const users = useMemberNames(shownTeams)
  const hasLedTeam = teams.some(({ role }) => role === 'leader')
  const page = filters.page ?? 1
  const pageCount = Math.ceil((data?.count ?? 0) / TASK_PAGE_SIZE)
  const isFiltered = Object.values(filters).some(Boolean)

  function update(change: TaskFilters) {
    onFiltersChange({ ...filters, ...change, page: undefined })
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex max-w-full gap-2 overflow-x-auto [scrollbar-width:none]">
          <button
            type="button"
            aria-pressed={!filters.status}
            onClick={() => update({ status: undefined })}
            className={FILTER_PILL}
          >
            All
          </button>
          {taskStatusSchema.options.map((status) => (
            <button
              key={status}
              type="button"
              aria-pressed={filters.status === status}
              onClick={() => update({ status })}
              className={FILTER_PILL}
            >
              {STATUS_LABELS[status]}
            </button>
          ))}
        </div>
        <div className="ml-auto">{action}</div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          aria-pressed={Boolean(filters.overdue)}
          onClick={() =>
            update({ overdue: filters.overdue ? undefined : true })
          }
          className={FILTER_PILL}
        >
          Overdue
        </button>
        {hasLedTeam && !teamId && (
          <button
            type="button"
            aria-pressed={filters.assignee === me.id}
            onClick={() =>
              update({
                assignee: filters.assignee === me.id ? undefined : me.id,
              })
            }
            className={FILTER_PILL}
          >
            Assigned to me
          </button>
        )}
        <Select
          aria-label="Filter by priority"
          className="h-11 w-auto lg:h-9"
          value={filters.priority ?? ''}
          onChange={({ target }) =>
            update({
              priority: taskPrioritySchema.safeParse(target.value).data,
            })
          }
        >
          <option value="">Any priority</option>
          {taskPrioritySchema.options.map((priority) => (
            <option key={priority} value={priority}>
              {PRIORITY_LABELS[priority]}
            </option>
          ))}
        </Select>
        {!teamId && teams.length > 1 && (
          <Select
            aria-label="Filter by team"
            className="h-11 w-auto max-w-56 lg:h-9"
            value={filters.team ?? ''}
            onChange={({ target }) =>
              update({ team: Number(target.value) || undefined })
            }
          >
            <option value="">All teams</option>
            {teams.map(({ id, name }) => (
              <option key={id} value={id}>
                {name}
              </option>
            ))}
          </Select>
        )}
        {teamId && canCreate && (
          <Select
            aria-label="Filter by person"
            className="h-11 w-auto max-w-56 lg:h-9"
            value={filters.assignee ?? ''}
            onChange={({ target }) =>
              update({ assignee: Number(target.value) || undefined })
            }
          >
            <option value="">Anyone</option>
            {[...users.values()].map((user) => (
              <option key={user.id} value={user.id}>
                {displayName(user)}
              </option>
            ))}
          </Select>
        )}
      </div>

      {error ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : data?.results.length === 0 ? (
        isFiltered ? (
          <EmptyState
            icon={ListChecks}
            title="No tasks match these filters"
            message="Clear the filters to see everything you have access to."
            action={
              <Button variant="outline" onClick={() => onFiltersChange({})}>
                Clear filters
              </Button>
            }
          />
        ) : (
          <EmptyState
            icon={ListChecks}
            title="No tasks yet"
            message={
              canCreate
                ? 'Create the first task, and give it a due date so it joins the queue.'
                : "When a team leader assigns you a task, you'll see it here."
            }
          />
        )
      ) : (
        <div className="@container rounded-lg border">
          <div
            aria-hidden="true"
            className={cn(
              ROW,
              'hidden border-b px-4 py-2 text-micro-uppercase text-muted-foreground uppercase @3xl:grid',
            )}
          >
            <span>Due</span>
            <span>Task</span>
            <span>Assigned to</span>
            <span>Priority</span>
            <span>Status</span>
          </div>
          {data ? (
            <ul
              className={cn(
                'divide-y transition-opacity duration-150',
                isPlaceholderData && 'opacity-60',
              )}
            >
              {data.results.map((task) => (
                <TaskRow
                  key={task.id}
                  task={task}
                  assignee={
                    task.assignee ? users.get(task.assignee) : undefined
                  }
                  teamName={
                    teamId
                      ? undefined
                      : teams.find(({ id }) => id === task.team)?.name
                  }
                />
              ))}
            </ul>
          ) : (
            <BoardSkeleton />
          )}
        </div>
      )}

      {pageCount > 1 && (
        <nav
          aria-label="Task pages"
          className="flex items-center justify-between gap-3"
        >
          <Button
            variant="outline"
            disabled={page <= 1}
            onClick={() => onFiltersChange({ ...filters, page: page - 1 })}
          >
            Previous
          </Button>
          <span className="text-body-sm text-muted-foreground tabular-nums">
            Page {page} of {pageCount}
          </span>
          <Button
            variant="outline"
            disabled={page >= pageCount}
            onClick={() => onFiltersChange({ ...filters, page: page + 1 })}
          >
            Next
          </Button>
        </nav>
      )}
    </div>
  )
}
