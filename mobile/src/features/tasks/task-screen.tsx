import { router, Stack } from 'expo-router';
import { useState } from 'react';
import { Alert, RefreshControl, ScrollView, StyleSheet, View } from 'react-native';

import { Composer, KeyboardView } from '@/components/screen';
import { ErrorState, ListSkeleton } from '@/components/states';
import { Badge, Button, Card, Chips, SectionTitle, ThemedText } from '@/components/ui';
import { Spacing } from '@/constants/theme';
import { useMembers, useTeam } from '@/features/teams/query';
import { displayName, formatDayTime } from '@/lib/format';
import { errorMessage } from '@/lib/http';

import { PRIORITY_LABELS, PRIORITY_TONES, STATUS_OPTIONS } from './labels';
import { useAddComment, useComments, useDeleteTask, useTask, useUpdateTask } from './query';
import type { Task } from './types';

function Property({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.property}>
      <ThemedText type="caption" color="mutedForeground">
        {label}
      </ThemedText>
      <ThemedText type="bodySm">{value}</ThemedText>
    </View>
  );
}

function Comments({ taskId }: { taskId: number }) {
  const { data, error, refetch, hasNextPage, fetchNextPage, isFetchingNextPage } = useComments(taskId);
  const comments = data?.pages.flatMap((page) => page.results);

  if (error) return <ErrorState error={error} onRetry={() => void refetch()} />;
  if (!comments) return <ListSkeleton rows={2} />;
  if (comments.length === 0) {
    return (
      <ThemedText type="bodySm" color="mutedForeground">
        No comments yet. Add the first one below.
      </ThemedText>
    );
  }
  return (
    <View style={styles.comments}>
      {comments.map((comment) => (
        <View key={comment.id} style={styles.comment}>
          <ThemedText type="captionBold">
            {displayName(comment.author)}
            <ThemedText type="caption" color="mutedForeground">
              {'  '}
              {formatDayTime(comment.created_at)}
            </ThemedText>
          </ThemedText>
          <ThemedText type="bodySm" selectable>
            {comment.body}
          </ThemedText>
        </View>
      ))}
      {hasNextPage ? (
        <Button
          label="Show more comments"
          variant="outline"
          onPress={() => void fetchNextPage()}
          loading={isFetchingNextPage}
        />
      ) : null}
    </View>
  );
}

function TaskDetails({ task }: { task: Task }) {
  const { team } = useTeam(task.team);
  const { data: members } = useMembers(task.team);
  const update = useUpdateTask(task.id);
  const remove = useDeleteTask(task.id);
  const isLeader = team?.role === 'leader';
  const assignee = members?.find(({ user }) => user.id === task.assignee)?.user;

  function confirmDelete() {
    Alert.alert('Delete this task?', 'Its comments go with it. This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete task',
        style: 'destructive',
        onPress: () =>
          remove.mutate(undefined, {
            onSuccess: () => router.back(),
            onError: (failure) => Alert.alert("Couldn't delete the task", errorMessage(failure)),
          }),
      },
    ]);
  }

  return (
    <>
      <ThemedText type="heading4" accessibilityRole="header" selectable>
        {task.title}
      </ThemedText>
      <View style={styles.badges}>
        <Badge label={`${PRIORITY_LABELS[task.priority]} priority`} tone={PRIORITY_TONES[task.priority]} />
        {task.is_overdue ? <Badge label="Overdue" tone="red" /> : null}
      </View>
      {task.description ? (
        <ThemedText type="bodyMd" selectable>
          {task.description}
        </ThemedText>
      ) : null}
      <Chips
        label="Status"
        options={STATUS_OPTIONS}
        value={task.status}
        disabled={update.isPending}
        onChange={(status) =>
          update.mutate(
            { status },
            { onError: (failure) => Alert.alert("Couldn't change the status", errorMessage(failure)) },
          )
        }
      />
      <Card>
        <Property label="Team" value={team?.name ?? '…'} />
        <Property
          label="Assignee"
          value={task.assignee === null ? 'Unassigned' : assignee ? displayName(assignee) : '…'}
        />
        <Property label="Due" value={formatDayTime(task.due_at)} />
        {task.completed_at ? <Property label="Completed" value={formatDayTime(task.completed_at)} /> : null}
      </Card>
      {isLeader ? (
        <View style={styles.actions}>
          <Button label="Edit task" variant="outline" onPress={() => router.push(`/tasks/${task.id}/edit`)} />
          <Button label="Delete task" variant="ghost" onPress={confirmDelete} loading={remove.isPending} />
        </View>
      ) : null}
    </>
  );
}

export function TaskScreen({ taskId }: { taskId: number }) {
  const { data: task, error, refetch, isRefetching } = useTask(taskId);
  const comments = useComments(taskId);
  const add = useAddComment(taskId);
  const [comment, setComment] = useState('');

  function send() {
    add.mutate(comment.trim(), {
      onSuccess: () => setComment(''),
      onError: (failure) => Alert.alert("Couldn't add the comment", errorMessage(failure)),
    });
  }

  return (
    <KeyboardView>
      <Stack.Screen options={{ title: 'Task' }} />
      <ScrollView
        contentContainerStyle={styles.content}
        keyboardShouldPersistTaps="handled"
        refreshControl={
          <RefreshControl
            refreshing={isRefetching}
            onRefresh={() => {
              void refetch();
              void comments.refetch();
            }}
          />
        }>
        {error ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : task ? (
          <>
            <TaskDetails task={task} />
            <SectionTitle>Comments</SectionTitle>
            <Comments taskId={taskId} />
          </>
        ) : (
          <ListSkeleton rows={3} />
        )}
      </ScrollView>
      {task ? (
        <Composer
          value={comment}
          onChangeText={setComment}
          onSend={send}
          pending={add.isPending}
          placeholder="Add a comment"
          maxLength={5000}
        />
      ) : null}
    </KeyboardView>
  );
}

const styles = StyleSheet.create({
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xxl },
  badges: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.xxs },
  property: { gap: 2 },
  actions: { gap: Spacing.xs },
  comments: { gap: Spacing.md },
  comment: { gap: 2 },
});
