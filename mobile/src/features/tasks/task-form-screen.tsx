import { router, Stack } from 'expo-router';

import { FormScroll } from '@/components/screen';
import { EmptyState, ErrorState, ListSkeleton } from '@/components/states';
import { Button, Chips, FormError, TextField } from '@/components/ui';
import { useMembers, useTeams } from '@/features/teams/query';
import { useSchemaForm } from '@/hooks/use-schema-form';
import { displayName } from '@/lib/format';

import { DueDateField } from './due-date-field';
import { PRIORITY_OPTIONS } from './labels';
import { useCreateTask, useTask, useUpdateTask } from './query';
import { newTaskSchema } from './schema';
import type { Task } from './types';

// Tomorrow at 17:00 local time: a sensible default that the picker makes easy to change.
function defaultDue() {
  const due = new Date();
  due.setDate(due.getDate() + 1);
  due.setHours(17, 0, 0, 0);
  return due;
}

function TaskForm({ task, teamId }: { task?: Task; teamId?: number }) {
  const { data: teams } = useTeams();
  const leaderTeams = teams?.filter(({ role }) => role === 'leader') ?? [];
  const create = useCreateTask();
  const update = useUpdateTask(task?.id ?? 0);
  const { values, set, errors, formError, submitting, handleSubmit } = useSchemaForm(
    newTaskSchema,
    {
      team: task?.team ?? teamId ?? (leaderTeams.length === 1 ? leaderTeams[0].id : 0),
      title: task?.title ?? '',
      description: task?.description ?? '',
      priority: task?.priority ?? 'medium',
      assignee: task?.assignee ?? null,
      due_at: task ? new Date(task.due_at) : defaultDue(),
    },
    async ({ team, ...fields }) => {
      // A task can't move between teams, so an edit sends everything but the team.
      if (task) await update.mutateAsync(fields);
      else await create.mutateAsync({ team, ...fields });
      router.back();
    },
  );
  const { data: members } = useMembers(values.team || undefined);

  if (teams && !task && leaderTeams.length === 0) {
    return (
      <EmptyState
        icon={{ ios: 'person.2', android: 'group' }}
        title="Only leaders create tasks"
        message="Create a team from the Teams tab to lead it, or ask a leader to add a task for you."
      />
    );
  }

  return (
    <>
      <FormError message={formError} />
      {task || teamId ? null : (
        <Chips
          label="Team"
          options={leaderTeams.map(({ id, name }) => ({ value: id, label: name }))}
          value={values.team}
          onChange={(team) => {
            set('team', team);
            set('assignee', null);
          }}
        />
      )}
      {errors.team ? <FormError message={errors.team} /> : null}
      <TextField
        label="Title"
        value={values.title}
        onChangeText={(text) => set('title', text)}
        error={errors.title}
        maxLength={200}
      />
      <TextField
        label="Description"
        value={values.description}
        onChangeText={(text) => set('description', text)}
        error={errors.description}
        multiline
        maxLength={10_000}
      />
      <Chips label="Priority" options={PRIORITY_OPTIONS} value={values.priority} onChange={(p) => set('priority', p)} />
      {values.team ? (
        <Chips
          label="Assignee"
          options={[
            { value: null, label: 'Unassigned' },
            ...(members ?? []).map(({ user }) => ({ value: user.id, label: displayName(user) })),
          ]}
          value={values.assignee}
          onChange={(assignee) => set('assignee', assignee)}
        />
      ) : null}
      {errors.assignee ? <FormError message={errors.assignee} /> : null}
      <DueDateField value={values.due_at} onChange={(date) => set('due_at', date)} error={errors.due_at} />
      <Button label={task ? 'Save changes' : 'Create task'} onPress={handleSubmit} loading={submitting} />
    </>
  );
}

export function NewTaskScreen({ teamId }: { teamId?: number }) {
  return (
    <FormScroll>
      <Stack.Screen options={{ title: 'New task' }} />
      <TaskForm teamId={teamId} />
    </FormScroll>
  );
}

export function EditTaskScreen({ taskId }: { taskId: number }) {
  const { data: task, error, refetch } = useTask(taskId);
  return (
    <FormScroll>
      <Stack.Screen options={{ title: 'Edit task' }} />
      {error ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : task ? (
        <TaskForm task={task} />
      ) : (
        <ListSkeleton rows={3} />
      )}
    </FormScroll>
  );
}
