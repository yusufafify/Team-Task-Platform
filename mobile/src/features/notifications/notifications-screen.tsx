import { Alert, FlatList, Pressable, RefreshControl, StyleSheet, View } from 'react-native';

import { EmptyState, ErrorState, ListSkeleton } from '@/components/states';
import { Button, ThemedText } from '@/components/ui';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { formatDayTime } from '@/lib/format';
import { errorMessage } from '@/lib/http';

import { useOpenNotification } from './hooks';
import { useMarkAllRead, useNotifications, useUnreadCount } from './query';
import type { Notification } from './types';

function NotificationRow({ notification, onPress }: { notification: Notification; onPress: () => void }) {
  const t = useTheme();
  const unread = notification.read_at === null;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityHint={unread ? 'Unread' : undefined}
      onPress={onPress}
      style={({ pressed }) => [
        styles.row,
        { backgroundColor: pressed ? t.muted : unread ? t.surfaceSoft : t.card, borderColor: t.border },
      ]}>
      <View style={[styles.dot, { backgroundColor: unread ? t.primary : 'transparent' }]} />
      <View style={styles.text}>
        <ThemedText type={unread ? 'captionBold' : 'caption'}>
          {notification.title}
          {unread ? ' · New' : ''}
        </ThemedText>
        <ThemedText type="bodySm" numberOfLines={2}>
          {notification.body}
        </ThemedText>
        <ThemedText type="caption" color="mutedForeground">
          {formatDayTime(notification.created_at)}
        </ThemedText>
      </View>
    </Pressable>
  );
}

export function NotificationsScreen() {
  const { data, error, refetch, isRefetching, hasNextPage, fetchNextPage, isFetchingNextPage } = useNotifications();
  const { data: unread } = useUnreadCount();
  const markAll = useMarkAllRead();
  const open = useOpenNotification();
  const notifications = data?.pages.flatMap((page) => page.results);

  return (
    <FlatList
      data={notifications}
      keyExtractor={(notification) => String(notification.id)}
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={styles.list}
      refreshControl={<RefreshControl refreshing={isRefetching && !isFetchingNextPage} onRefresh={() => void refetch()} />}
      onEndReached={() => hasNextPage && !isFetchingNextPage && void fetchNextPage()}
      onEndReachedThreshold={0.5}
      renderItem={({ item }) => <NotificationRow notification={item} onPress={() => void open(item)} />}
      ListHeaderComponent={
        unread ? (
            <View style={styles.header}>
              <Button
                label={`Mark all ${unread} as read`}
                variant="outline"
                loading={markAll.isPending}
                onPress={() =>
                  markAll.mutate(undefined, {
                    onError: (failure) => Alert.alert("Couldn't mark them read", errorMessage(failure)),
                  })
                }
              />
            </View>
        ) : undefined
      }
      ListEmptyComponent={
        error ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : !notifications ? (
          <ListSkeleton />
        ) : (
          <EmptyState
            icon={{ ios: 'bell', android: 'notifications' }}
            title="You're all caught up"
            message="Assignments, comments, reminders and new reports show up here."
          />
        )
      }
      ListFooterComponent={isFetchingNextPage ? <ListSkeleton rows={1} /> : undefined}
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: Spacing.md, gap: Spacing.xs, paddingBottom: Spacing.xxxl },
  header: { marginBottom: Spacing.xs },
  row: {
    flexDirection: 'row',
    gap: Spacing.sm,
    borderWidth: 1,
    borderRadius: Radius.lg,
    padding: Spacing.md,
  },
  dot: { width: 8, height: 8, borderRadius: Radius.full, marginTop: 6 },
  text: { flex: 1, gap: 2 },
});
