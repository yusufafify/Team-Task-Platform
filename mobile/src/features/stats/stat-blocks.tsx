import { StyleSheet, View } from 'react-native';

import { Card, ThemedText } from '@/components/ui';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { formatPercent } from '@/lib/format';

import type { Stats } from './types';

function formatDelay(days: number | null) {
  if (days === null) return 'No data';
  const rounded = Math.round(days * 10) / 10;
  return `${rounded} ${rounded === 1 ? 'day' : 'days'}`;
}

export function StatTiles({ stats }: { stats: Stats }) {
  const t = useTheme();
  const tiles = [
    { label: 'Completion rate', value: formatPercent(stats.completion_rate) },
    { label: 'On-time rate', value: formatPercent(stats.on_time_rate) },
    { label: 'Due', value: stats.due },
    { label: 'Completed', value: stats.completed },
    { label: 'On time', value: stats.on_time },
    { label: 'Delayed', value: stats.delayed },
    { label: 'Overdue now', value: stats.overdue },
    { label: 'Average delay', value: formatDelay(stats.average_delay_days) },
  ];

  return (
    <View style={[styles.grid, { borderColor: t.border, backgroundColor: t.border }]}>
      {tiles.map(({ label, value }) => (
        <View key={label} style={[styles.tile, { backgroundColor: t.card }]} accessible accessibilityLabel={`${label}: ${value}`}>
          <ThemedText type="caption" color="mutedForeground">
            {label}
          </ThemedText>
          <ThemedText type="heading4" style={styles.number}>
            {value}
          </ThemedText>
        </View>
      ))}
    </View>
  );
}

// Phones are too narrow for web's table, so each member is a compact card.
export function MemberStats({ rows }: { rows: readonly { key: string | number; name: string; stats: Stats }[] }) {
  return (
    <View style={styles.members}>
      {rows.map(({ key, name, stats }) => (
        <Card key={key}>
          <ThemedText type="bodyMd">{name}</ThemedText>
          <ThemedText type="caption" color="mutedForeground" style={styles.number}>
            {stats.completed} of {stats.due} due completed · {stats.overdue} overdue now
          </ThemedText>
          <ThemedText type="caption" color="mutedForeground" style={styles.number}>
            Completion {formatPercent(stats.completion_rate)} · On time {formatPercent(stats.on_time_rate)} · Average
            delay {formatDelay(stats.average_delay_days)}
          </ThemedText>
        </Card>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: StyleSheet.hairlineWidth,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: Radius.lg,
    overflow: 'hidden',
  },
  tile: { flexGrow: 1, flexBasis: '45%', padding: Spacing.md, gap: Spacing.xxs },
  number: { fontVariant: ['tabular-nums'] },
  members: { gap: Spacing.xs },
});
