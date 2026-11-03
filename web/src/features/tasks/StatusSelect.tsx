import { Select } from '@/components/ui/select'
import { cn, extractErrorMessage } from '@/lib/utils'
import { STATUS_LABELS } from './labels'
import { useUpdateTask } from './query'
import { taskStatusSchema } from './schema'
import type { Task } from './types'

interface StatusSelectProps {
  task: Task
  className?: string
}

export function StatusSelect({ task, className }: StatusSelectProps) {
  const update = useUpdateTask(task.id)
  const pendingStatus =
    update.isPending && 'status' in update.variables
      ? update.variables.status
      : undefined

  return (
    <div className="flex flex-col gap-1">
      <Select
        aria-label={`Status of ${task.title}`}
        className={cn('h-11 @3xl:h-9', className)}
        value={pendingStatus ?? task.status}
        disabled={update.isPending}
        onChange={(event) =>
          update.mutate({ status: taskStatusSchema.parse(event.target.value) })
        }
      >
        {taskStatusSchema.options.map((status) => (
          <option key={status} value={status}>
            {STATUS_LABELS[status]}
          </option>
        ))}
      </Select>
      {update.error && (
        <p role="alert" className="text-caption text-destructive-text">
          {extractErrorMessage(update.error)}
        </p>
      )}
    </div>
  )
}
