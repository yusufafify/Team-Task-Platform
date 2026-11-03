import { useState } from 'react'
import type { ReactElement } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Field, FormError } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { useMembers, useTeams } from '@/features/teams/query'
import { useSchemaForm } from '@/hooks/useSchemaForm'
import { displayName, toDateTimeLocal } from '@/lib/format'
import { PRIORITY_LABELS } from './labels'
import { useCreateTask, useUpdateTask } from './query'
import { newTaskSchema, taskFormSchema, taskPrioritySchema } from './schema'
import type { Task } from './types'

interface TaskFieldsProps {
  task?: Task
  teamId?: number
  errors: Record<string, string>
}

function TaskFields({ task, teamId, errors }: TaskFieldsProps) {
  const { data: members } = useMembers(teamId)

  return (
    <>
      <Field label="Title" error={errors.title}>
        <Input
          name="title"
          defaultValue={task?.title}
          maxLength={200}
          required
        />
      </Field>
      <Field label="Description" error={errors.description}>
        <Textarea
          name="description"
          defaultValue={task?.description}
          maxLength={10_000}
        />
      </Field>
      <div className="grid gap-5 sm:grid-cols-2">
        <Field label="Priority" error={errors.priority}>
          <Select name="priority" defaultValue={task?.priority ?? 'medium'}>
            {taskPrioritySchema.options.map((priority) => (
              <option key={priority} value={priority}>
                {PRIORITY_LABELS[priority]}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Assigned to" error={errors.assignee}>
          {/* The key resets the choice once the roster loads or the team changes. */}
          <Select
            key={`${teamId}-${members?.length}`}
            name="assignee"
            defaultValue={task?.assignee ?? ''}
          >
            <option value="">Unassigned</option>
            {members?.map(({ user }) => (
              <option key={user.id} value={user.id}>
                {displayName(user)}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      <Field label="Due" error={errors.due_at}>
        <Input
          name="due_at"
          type="datetime-local"
          defaultValue={task && toDateTimeLocal(task.due_at)}
          required
        />
      </Field>
    </>
  )
}

interface EditTaskDialogProps {
  task: Task
  trigger: ReactElement
}

export function EditTaskDialog({ task, trigger }: EditTaskDialogProps) {
  const [open, setOpen] = useState(false)
  const update = useUpdateTask(task.id)
  const { errors, formError, handleSubmit } = useSchemaForm(
    taskFormSchema,
    async (values) => {
      await update.mutateAsync(values)
      setOpen(false)
    },
  )

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent aria-describedby={undefined}>
        <DialogTitle>Edit task</DialogTitle>
        <form
          onSubmit={handleSubmit}
          noValidate
          className="flex flex-col gap-5"
        >
          <FormError>{formError}</FormError>
          <TaskFields task={task} teamId={task.team} errors={errors} />
          <Button
            type="submit"
            disabled={update.isPending}
            className="self-end"
          >
            Save changes
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

interface NewTaskDialogProps {
  teamId?: number
}

export function NewTaskDialog({ teamId }: NewTaskDialogProps) {
  const [open, setOpen] = useState(false)
  const create = useCreateTask()
  const { data: teams } = useTeams()
  const ledTeams = teams?.filter(({ role }) => role === 'leader') ?? []
  const [chosenTeam, setChosenTeam] = useState<number>()
  const selectedTeam = teamId ?? chosenTeam ?? ledTeams[0]?.id
  const { errors, formError, handleSubmit } = useSchemaForm(
    newTaskSchema,
    async (values) => {
      await create.mutateAsync(values)
      setOpen(false)
    },
  )

  if (ledTeams.length === 0) return null

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>New task</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>New task</DialogTitle>
        <DialogDescription>
          The person you assign gets a notification straight away.
        </DialogDescription>
        <form
          onSubmit={handleSubmit}
          noValidate
          className="flex flex-col gap-5"
        >
          <FormError>{formError}</FormError>
          {teamId === undefined ? (
            <Field label="Team" error={errors.team}>
              <Select
                name="team"
                value={selectedTeam}
                onChange={(event) => setChosenTeam(Number(event.target.value))}
              >
                {ledTeams.map(({ id, name }) => (
                  <option key={id} value={id}>
                    {name}
                  </option>
                ))}
              </Select>
            </Field>
          ) : (
            <input type="hidden" name="team" value={teamId} />
          )}
          <TaskFields teamId={selectedTeam} errors={errors} />
          <Button
            type="submit"
            disabled={create.isPending}
            className="self-end"
          >
            Create task
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
