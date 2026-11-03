import { Stack } from 'expo-router';
import { useState } from 'react';
import { Alert, FlatList, StyleSheet, View } from 'react-native';

import { Composer, KeyboardView } from '@/components/screen';
import { EmptyState, ErrorState, ListSkeleton } from '@/components/states';
import { ThemedText } from '@/components/ui';
import { Radius, Spacing } from '@/constants/theme';
import { useMe } from '@/features/auth/query';
import { useLiveDown } from '@/features/live/hooks';
import { useTeam } from '@/features/teams/query';
import { useTheme } from '@/hooks/use-theme';
import { displayName, formatDayTime } from '@/lib/format';
import { errorMessage } from '@/lib/http';

import { useMessages, useSendMessage } from './query';
import type { Message } from './types';

function Bubble({ message, mine }: { message: Message; mine: boolean }) {
  const t = useTheme();
  return (
    <View style={[styles.bubbleWrap, mine && styles.mine]}>
      <ThemedText type="caption" color="mutedForeground">
        {mine ? 'You' : displayName(message.author)} · {formatDayTime(message.created_at)}
      </ThemedText>
      <View
        style={[
          styles.bubble,
          mine ? { backgroundColor: t.secondary } : { backgroundColor: t.card, borderColor: t.border, borderWidth: 1 },
        ]}>
        <ThemedText type="bodySm" selectable>
          {message.body}
        </ThemedText>
      </View>
    </View>
  );
}

export function LiveDownNote() {
  const t = useTheme();
  if (!useLiveDown()) return null;
  return (
    <View accessibilityRole="alert" style={[styles.note, { backgroundColor: t.tintYellow }]}>
      <ThemedText type="caption" color="onTint">
        Live updates are paused while we reconnect, so new messages may be slow to appear.
      </ThemedText>
    </View>
  );
}

export function ChatScreen({ teamId }: { teamId: number }) {
  const { team } = useTeam(teamId);
  const { data: me } = useMe();
  const { data, error, refetch, hasNextPage, fetchNextPage, isFetchingNextPage } = useMessages(teamId);
  const send = useSendMessage(teamId);
  const [draft, setDraft] = useState('');
  const messages = data?.pages.flatMap((page) => page.results);

  function submit() {
    send.mutate(draft.trim(), {
      onSuccess: () => setDraft(''),
      onError: (failure) => Alert.alert("Couldn't send the message", errorMessage(failure)),
    });
  }

  return (
    <KeyboardView>
      <Stack.Screen options={{ title: team ? `${team.name} chat` : 'Chat' }} />
      <LiveDownNote />
      {error ? (
        <View style={styles.padded}>
          <ErrorState error={error} onRetry={() => void refetch()} />
        </View>
      ) : !messages ? (
        <View style={styles.padded}>
          <ListSkeleton />
        </View>
      ) : messages.length === 0 ? (
        <View style={styles.padded}>
          <EmptyState
            icon={{ ios: 'bubble.left.and.bubble.right', android: 'forum' }}
            title="No messages yet"
            message="Say hello. Everyone on the team sees what you post here."
          />
        </View>
      ) : (
        // Newest first from the API, so an inverted list keeps the latest at the bottom.
        <FlatList
          inverted
          data={messages}
          keyExtractor={(message) => String(message.id)}
          renderItem={({ item }) => <Bubble message={item} mine={item.author.id === me?.id} />}
          contentContainerStyle={styles.list}
          keyboardShouldPersistTaps="handled"
          onEndReached={() => hasNextPage && !isFetchingNextPage && void fetchNextPage()}
          onEndReachedThreshold={0.5}
          ListFooterComponent={isFetchingNextPage ? <ListSkeleton rows={1} /> : undefined}
        />
      )}
      <Composer
        value={draft}
        onChangeText={setDraft}
        onSend={submit}
        pending={send.isPending}
        placeholder="Message the team"
        maxLength={5000}
      />
    </KeyboardView>
  );
}

const styles = StyleSheet.create({
  padded: { flex: 1, padding: Spacing.md },
  list: { padding: Spacing.md, gap: Spacing.sm },
  bubbleWrap: { alignItems: 'flex-start', gap: 2, maxWidth: '85%' },
  mine: { alignSelf: 'flex-end', alignItems: 'flex-end' },
  bubble: { borderRadius: Radius.lg, paddingHorizontal: Spacing.sm, paddingVertical: Spacing.xs },
  note: { paddingHorizontal: Spacing.md, paddingVertical: Spacing.xs },
});
