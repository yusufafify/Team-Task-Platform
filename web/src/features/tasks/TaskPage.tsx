import { Link, useNavigate } from '@tanstack/react-router'
import { AlertTriangle } from 'lucide-react'
import type { ReactNode } from 'react'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { Page } from '@/components/shared/Page'
import { ErrorState } from '@/components/shared/States'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Field, FormError } from '@/components/ui/field'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { useMembers, useTeams } from '@/features/teams/query'
import { useSchemaForm } from '@/hooks/useSchemaForm'
import { displayName, formatDayTime } from '@/lib/format'
import { PRIORITY_BADGES, PRIORITY_LABELS } from './labels'
import { useAddComment, useComments, useDeleteTask, useTask } from './query'
import { commentSchema } from './schema'
import { StatusSelect } from './StatusSelect'
import { EditTaskDialog } from './TaskFormDialog'
import type { Task } from './types'

interface CommentsProps {
  taskId: number
}

function Comments({ taskId }: CommentsProps) {
  const {
    data,
    error,
    refetch,
    hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
  } = useComments(taskId)
  const add = useAddComment(taskId)
  const { errors, formError, handleSubmit } = useSchemaForm(
    commentSchema,
    async ({ body }, form) => {
      await add.mutateAsync(body)
      form.reset()
    },
  )
  const comments = data?.pages.flatMap((page) => page.results)

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-heading-5">Comments</h2>
      {error ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : !comments ? (
        <Skeleton className="h-16" aria-busy="true" />
      ) : comments.length === 0 ? (
        <p className="text-body-sm text-muted-foreground">
          No comments yet. Add the first one below.
        </p>
      ) : (
        <ul className="flex flex-col gap-4">
          {comments.map((comment) => (
            <li key={comment.id} className="flex flex-col gap-1">
              <p className="flex flex-wrap items-baseline gap-x-2">
                <span className="text-body-sm font-medium">
                  {displayName(comment.author)}
                </span>
                <span className="text-caption text-muted-foreground tabular-nums">
                  {formatDayTime(comment.created_at)}
                </span>
              </p>
              <p className="text-body-sm whitespace-pre-wrap">{comment.body}</p>
            </li>
          ))}
        </ul>
      )}
      {hasNextPage && (
        <Button
          variant="outline"
          size="sm"
          disabled={isFetchingNextPage}
          onClick={() => void fetchNextPage()}
          className="self-start"
        >
          Show more comments
        </Button>
      )}
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-3">
        <FormError>{formError}</FormError>
        <Field label="Add a comment" error={errors.body}>
          <Textarea name="body" maxLength={5000} required />
        </Field>
        <Button
          type="submit"
          variant="outline"
          disabled={add.isPending}
          className="self-end"
        >
          Add comment
        </Button>
      </form>
    </section>
  )
}

interface PropertyProps {
  label: string
  children: ReactNode
}

function Property({ label, children }: PropertyProps) {
  return (
    <div className="flex flex-col gap-1">
      <dt className="text-caption text-muted-foreground">{label}</dt>
      <dd className="text-body-sm">{children}</dd>
    </div>
  )
}

interface TaskDetailsProps {
  task: Task
}

function TaskDetails({ task }: TaskDetailsProps) {
  const { data: teams } = useTeams()
  const { data: members } = useMembers(task.team)
  const remove = useDeleteTask(task.id)
  const navigate = useNavigate()
  const team = teams?.find(({ id }) => id === task.team)
  const assignee = members?.find(({ user }) => user.id === task.assignee)
  const creator = members?.find(({ user }) => user.id === task.created_by)

  async function deleteTask() {
    await remove.mutateAsync()
    await navigate({ to: '/' })
  }

  return (
    <Page
      title={task.title}
      action={
        team?.role === 'leader' && (
          <div className="flex gap-3">
            <EditTaskDialog
              task={task}
              trigger={<Button variant="outline">Edit task</Button>}
            />
            <ConfirmDialog
              trigger={<Button variant="outline">Delete task</Button>}
              title="Delete this task?"
              message="Its comments go with it, and this can't be undone."
              confirmLabel="Delete task"
              onConfirm={deleteTask}
            />
          </div>
        )
      }
    >
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_240px]">
        <div className="flex min-w-0 flex-col gap-8">
          <p className="text-body-md whitespace-pre-wrap">
            {task.description || (
              <span className="text-muted-foreground">No description.</span>
            )}
          </p>
          <Comments taskId={task.id} />
        </div>

        <dl className="flex flex-col gap-4 rounded-lg border p-5 lg:self-start">
          <Property label="Status">
            <StatusSelect task={task} />
          </Property>
          <Property label="Priority">
            <Badge variant={PRIORITY_BADGES[task.priority]}>
              {PRIORITY_LABELS[task.priority]}
            </Badge>
          </Property>
          <Property label="Due">
            <span className="font-semibold tabular-nums">
              {formatDayTime(task.due_at)}
            </span>
            {task.is_overdue && (
              <span className="mt-1 flex items-center gap-1 text-caption text-destructive-text">
                <AlertTriangle className="size-3" aria-hidden="true" />
                Overdue
              </span>
            )}
          </Property>
          <Property label="Assigned to">
            {assignee ? displayName(assignee.user) : 'Unassigned'}
          </Property>
          {team && (
            <Property label="Team">
              <Link
                to="/teams/$teamId"
                params={{ teamId: team.id }}
                className="text-link hover-device:hover:underline"
              >
                {team.name}
              </Link>
            </Property>
          )}
          {creator && (
            <Property label="Created by">{displayName(creator.user)}</Property>
          )}
          {task.completed_at && (
            <Property label="Completed">
              <span className="tabular-nums">
                {formatDayTime(task.completed_at)}
              </span>
            </Property>
          )}
        </dl>
      </div>
    </Page>
  )
}

interface TaskPageProps {
  taskId: number
}

export function TaskPage({ taskId }: TaskPageProps) {
  const { data: task, error, refetch } = useTask(taskId)

  if (error) {
    return (
      <Page title="Task">
        <ErrorState error={error} onRetry={() => void refetch()} />
      </Page>
    )
  }
  if (!task) {
    return (
      <div
        aria-busy="true"
        className="mx-auto flex max-w-5xl flex-col gap-6 px-4 py-8 sm:px-8"
      >
        <Skeleton className="h-9 w-2/3" />
        <Skeleton className="h-40" />
      </div>
    )
  }
  return <TaskDetails task={task} />
}
