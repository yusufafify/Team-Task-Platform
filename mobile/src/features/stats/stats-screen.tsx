import { Stack } from 'expo-router';
import { useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet } from 'react-native';

import { ErrorState, ListSkeleton } from '@/components/states';
import { Chips, SectionTitle, ThemedText } from '@/components/ui';
import { Spacing } from '@/constants/theme';
import { formatDate, displayName, toDateParam } from '@/lib/format';

import { useTeamStats } from './query';
import { MemberStats, StatTiles } from './stat-blocks';
import type { StatsPeriod } from './types';

type Period = 'this_month' | 'last_month' | 'last_90_days';

const PERIODS: { value: Period; label: string }[] = [
  { value: 'this_month', label: 'This month' },
  { value: 'last_month', label: 'Last month' },
  { value: 'last_90_days', label: 'Last 90 days' },
];

// Device-local days; the server counts them in the team's timezone, which is usually the same.
function toRange(period: Period): StatsPeriod {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth();
  if (period === 'this_month') return { start: toDateParam(new Date(year, month, 1)), end: toDateParam(today) };
  if (period === 'last_month') {
    return { start: toDateParam(new Date(year, month - 1, 1)), end: toDateParam(new Date(year, month, 0)) };
  }
  return { start: toDateParam(new Date(year, month, today.getDate() - 89)), end: toDateParam(today) };
}

export function StatsScreen({ teamId }: { teamId: number }) {
  const [period, setPeriod] = useState<Period>('this_month');
  const { data, error, refetch, isRefetching, isPlaceholderData } = useTeamStats(teamId, toRange(period));

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={isRefetching && !isPlaceholderData} onRefresh={() => void refetch()} />}>
      <Stack.Screen options={{ title: 'Stats' }} />
      <Chips label="Period" options={PERIODS} value={period} onChange={setPeriod} />
      {error ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : !data ? (
        <ListSkeleton />
      ) : (
        <>
          <ThemedText type="caption" color="mutedForeground">
            {data.scope === 'team' ? 'Whole team' : 'Your numbers'}, {formatDate(data.start)} to {formatDate(data.end)}{' '}
            ({data.timezone})
          </ThemedText>
          <StatTiles stats={data.stats} />
          {data.scope === 'team' && data.members.length ? (
            <>
              <SectionTitle>Per member</SectionTitle>
              <MemberStats
                rows={data.members.map(({ user, stats }) => ({ key: user.id, name: displayName(user), stats }))}
              />
            </>
          ) : null}
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xxxl },
});
