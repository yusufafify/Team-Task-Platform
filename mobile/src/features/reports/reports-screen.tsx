import { Stack } from 'expo-router';
import { useState } from 'react';
import { FlatList, RefreshControl, StyleSheet, View } from 'react-native';

import { EmptyState, ErrorState, ListSkeleton } from '@/components/states';
import { Button, Card, SectionTitle, ThemedText } from '@/components/ui';
import { Spacing } from '@/constants/theme';
import { MemberStats, StatTiles } from '@/features/stats/stat-blocks';
import { useTeam } from '@/features/teams/query';
import { formatMonth } from '@/lib/format';

import { useReports } from './query';
import type { MonthlyReport } from './types';

function ReportCard({ report }: { report: MonthlyReport }) {
  const [showNumbers, setShowNumbers] = useState(false);
  return (
    <Card style={styles.card}>
      <ThemedText type="heading5" accessibilityRole="header">
        {formatMonth(report.month)}
      </ThemedText>
      {/* Plain text with its line breaks: the AI wrote it and it can quote other people. */}
      <ThemedText type="bodySm" selectable>
        {report.body}
      </ThemedText>
      <Button
        label={showNumbers ? 'Hide the numbers' : 'Show the numbers'}
        variant="outline"
        onPress={() => setShowNumbers((shown) => !shown)}
      />
      {showNumbers ? (
        <>
          <ThemedText type="caption" color="mutedForeground">
            Frozen when the report was written, so they can differ from live stats.
          </ThemedText>
          <StatTiles stats={report.stats} />
          {report.members.length ? (
            <>
              <SectionTitle>Per member</SectionTitle>
              <MemberStats rows={report.members.map(({ name, stats }) => ({ key: name, name, stats }))} />
            </>
          ) : null}
        </>
      ) : null}
    </Card>
  );
}

export function ReportsScreen({ teamId }: { teamId: number }) {
  const { team } = useTeam(teamId);
  const isLeader = team?.role === 'leader';
  const { data, error, refetch, isRefetching, hasNextPage, fetchNextPage, isFetchingNextPage } = useReports(
    teamId,
    isLeader,
  );
  const reports = data?.pages.flatMap((page) => page.results);

  return (
    <FlatList
      data={reports}
      keyExtractor={(report) => String(report.id)}
      renderItem={({ item }) => <ReportCard report={item} />}
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={styles.list}
      refreshControl={<RefreshControl refreshing={isRefetching && !isFetchingNextPage} onRefresh={() => void refetch()} />}
      onEndReached={() => hasNextPage && !isFetchingNextPage && void fetchNextPage()}
      onEndReachedThreshold={0.5}
      ListHeaderComponent={<Stack.Screen options={{ title: 'Reports' }} />}
      ListEmptyComponent={
        <View>
          {team && !isLeader ? (
            <EmptyState
              icon={{ ios: 'lock', android: 'lock' }}
              title="Reports are for leaders"
              message="A monthly report rates every member, so only the team's leaders can read it."
            />
          ) : error ? (
            <ErrorState error={error} onRetry={() => void refetch()} />
          ) : !reports ? (
            <ListSkeleton />
          ) : (
            <EmptyState
              icon={{ ios: 'doc.text', android: 'description' }}
              title="No reports yet"
              message="A report is written within a day of each month ending. A month with no activity gets none."
            />
          )}
        </View>
      }
      ListFooterComponent={isFetchingNextPage ? <ListSkeleton rows={1} /> : undefined}
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xxxl },
  card: { gap: Spacing.sm },
});
