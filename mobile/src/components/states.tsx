import type { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { Button, Icon, ThemedText, type IconName } from '@/components/ui';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { HttpError } from '@/lib/http';

// Static blocks shaped like list rows, so nothing animates for people who reduce motion.
export function ListSkeleton({ rows = 4 }: { rows?: number }) {
  const t = useTheme();
  return (
    <View style={styles.skeleton} accessibilityLabel="Loading" accessibilityRole="progressbar">
      {Array.from({ length: rows }, (_, index) => (
        <View key={index} style={[styles.skeletonRow, { backgroundColor: t.muted }]} />
      ))}
    </View>
  );
}

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const t = useTheme();
  // The API answers 404 for anything hidden from this person, so retrying can't help.
  const isMissing = error instanceof HttpError && error.status === 404;
  const requestId = error instanceof HttpError && error.status >= 500 ? error.requestId : null;

  return (
    <View accessibilityRole="alert" style={[styles.box, { borderColor: t.border }]}>
      <ThemedText type="heading5">{isMissing ? "This isn't available" : "This couldn't load"}</ThemedText>
      <ThemedText type="bodySm" color="mutedForeground">
        {isMissing
          ? 'It may have been deleted, or you may not have access to it.'
          : error instanceof Error
            ? error.message
            : String(error)}
      </ThemedText>
      {requestId ? (
        <ThemedText type="caption" color="mutedForeground" selectable>
          Reference: {requestId}
        </ThemedText>
      ) : null}
      {onRetry && !isMissing ? <Button label="Try again" variant="outline" onPress={onRetry} /> : null}
    </View>
  );
}

interface EmptyStateProps {
  icon: IconName;
  title: string;
  message: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, message, action }: EmptyStateProps) {
  const t = useTheme();
  return (
    <View style={[styles.box, styles.empty, { borderColor: t.border }]}>
      <View style={[styles.emptyIcon, { backgroundColor: t.secondary }]}>
        <Icon name={icon} size={24} color="mutedForeground" />
      </View>
      <ThemedText type="heading5" style={styles.center}>
        {title}
      </ThemedText>
      <ThemedText type="bodySm" color="mutedForeground" style={styles.center}>
        {message}
      </ThemedText>
      {action}
    </View>
  );
}

const styles = StyleSheet.create({
  skeleton: { gap: Spacing.xs },
  skeletonRow: { height: 64, borderRadius: Radius.lg },
  box: { gap: Spacing.xs, borderWidth: 1, borderRadius: Radius.lg, padding: Spacing.lg },
  empty: { alignItems: 'center', borderStyle: 'dashed', paddingVertical: Spacing.sectionSm },
  emptyIcon: {
    width: 48,
    height: 48,
    borderRadius: Radius.lg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  center: { textAlign: 'center' },
});
