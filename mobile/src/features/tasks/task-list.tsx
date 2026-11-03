import { router } from 'expo-router';
import { useState, type ReactElement } from 'react';
import { FlatList, Pressable, RefreshControl, StyleSheet, View } from 'react-native';

import { EmptyState, ErrorState, ListSkeleton } from '@/components/states';
import { Badge, Button, Chips, ThemedText } from '@/components/ui';
import { Radius, Spacing } from '@/constants/theme';
import { useTeams } from '@/features/teams/query';
import { useTheme } from '@/hooks/use-theme';
import { formatDayTime } from '@/lib/format';

import { PRIORITY_LABELS, PRIORITY_TONES, STATUS_LABELS, STATUS_OPTIONS, STATUS_TONES } from './labels';
import { useTasks } from './query';
import type { Task, TaskStatus } from './types';

type Filter = 'all' | TaskStatus | 'overdue';

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'All' },
  ...STATUS_OPTIONS,
  { value: 'overdue', label: 'Overdue' },
];

function TaskRow({ task, teamName }: { task: Task; teamName?: string }) {
  const t = useTheme();
  return (
    <Pressable
      accessibilityRole="button"
      onPress={() => router.push(`/tasks/${task.id}`)}
      style={({ pressed }) => [styles.row, { backgroundColor: pressed ? t.muted : t.card, borderColor: t.border }]}>
      <ThemedText type="bodyMd" numberOfLines={2}>
        {task.title}
      </ThemedText>
      <ThemedText type="caption" color={task.is_overdue ? 'destructiveText' : 'mutedForeground'}>
        {task.is_overdue ? 'Overdue · ' : 'Due '}
        {formatDayTime(task.due_at)}
        {teamName ? ` · ${teamName}` : ''}
      </ThemedText>
      <View style={styles.badges}>
        <Badge label={STATUS_LABELS[task.status]} tone={STATUS_TONES[task.status]} />
        <Badge label={PRIORITY_LABELS[task.priority]} tone={PRIORITY_TONES[task.priority]} />
      </View>
    </Pressable>
  );
}

interface TaskListProps {
  team?: number;
  header?: ReactElement;
}

export function TaskList({ team, header }: TaskListProps) {
  const [filter, setFilter] = useState<Filter>('all');
  const filters = {
    team,
    status: filter === 'all' || filter === 'overdue' ? undefined : filter,
    overdue: filter === 'overdue',
  };
  const { data, error, refetch, isRefetching, hasNextPage, fetchNextPage, isFetchingNextPage } = useTasks(filters);
  const { data: teams } = useTeams();
  const teamNames = new Map(teams?.map(({ id, name }) => [id, name]));
  const tasks = data?.pages.flatMap((page) => page.results);

  return (
    <FlatList
      data={tasks}
      keyExtractor={(task) => String(task.id)}
      renderItem={({ item }) => <TaskRow task={item} teamName={team ? undefined : teamNames.get(item.team)} />}
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={styles.list}
      refreshControl={<RefreshControl refreshing={isRefetching && !isFetchingNextPage} onRefresh={() => void refetch()} />}
      onEndReached={() => hasNextPage && !isFetchingNextPage && void fetchNextPage()}
      onEndReachedThreshold={0.5}
      ListHeaderComponent={
        <View style={styles.header}>
          {header}
          <Chips options={FILTERS} value={filter} onChange={setFilter} label="Show" />
        </View>
      }
      ListEmptyComponent={
        error ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : !tasks ? (
          <ListSkeleton />
        ) : (
          <EmptyState
            icon={{ ios: 'checklist', android: 'checklist' }}
            title={filter === 'all' ? 'No tasks yet' : 'Nothing matches this filter'}
            message={
              filter === 'all'
                ? 'Tasks a leader assigns to you, or creates in a team you lead, show up here.'
                : 'Try another filter to see the rest of your tasks.'
            }
          />
        )
      }
      ListFooterComponent={isFetchingNextPage ? <ListSkeleton rows={1} /> : undefined}
    />
  );
}

export function MyTasksScreen() {
  const { data: teams } = useTeams();
  const leads = teams?.some(({ role }) => role === 'leader');
  return (
    <TaskList
      header={leads ? <Button label="New task" variant="outline" onPress={() => router.push('/tasks/new')} /> : undefined}
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: Spacing.md, gap: Spacing.xs, paddingBottom: Spacing.xxxl },
  header: { gap: Spacing.md, marginBottom: Spacing.xs },
  row: { borderWidth: 1, borderRadius: Radius.lg, padding: Spacing.md, gap: Spacing.xxs },
  badges: { flexDirection: 'row', gap: Spacing.xxs, marginTop: Spacing.xxs },
});
