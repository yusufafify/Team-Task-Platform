import { Stack } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Alert, FlatList, Pressable, StyleSheet, View } from 'react-native';

import { Composer, KeyboardView } from '@/components/screen';
import { EmptyState, ErrorState, ListSkeleton } from '@/components/states';
import { ThemedText } from '@/components/ui';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { errorCode, errorMessage, HttpError } from '@/lib/http';

import { useAskAssistant, useAssistantThread, useClearThread } from './query';
import type { AssistantMessage } from './types';

function waitText(seconds: number | null) {
  if (!seconds) return 'later';
  if (seconds < 90) return `in ${seconds} seconds`;
  if (seconds < 5400) return `in about ${Math.round(seconds / 60)} minutes`;
  return `in about ${Math.round(seconds / 3600)} hours`;
}

function askErrorText(error: unknown) {
  const code = errorCode(error);
  if (code === 'throttled') {
    const retryAfter = error instanceof HttpError ? error.retryAfter : null;
    return `The assistant's limit is used up for now. Try again ${waitText(retryAfter)}.`;
  }
  if (code === 'ai_unavailable') return 'The assistant is unavailable right now. Try again later.';
  return errorMessage(error);
}

// Plain text only: answers can repeat what other people wrote, so nothing is rendered or linked.
function Turn({ message }: { message: AssistantMessage }) {
  const t = useTheme();
  const mine = message.role === 'user';
  return (
    <View
      style={[
        styles.turn,
        mine
          ? [styles.mine, { backgroundColor: t.secondary }]
          : { backgroundColor: t.card, borderColor: t.border, borderWidth: 1 },
      ]}>
      <ThemedText type="caption" color="mutedForeground">
        {mine ? 'You' : 'Assistant'}
      </ThemedText>
      <ThemedText type="bodySm" selectable>
        {message.body}
      </ThemedText>
    </View>
  );
}

export function AssistantScreen({ teamId }: { teamId: number }) {
  const t = useTheme();
  const { data, error, refetch, hasNextPage, fetchNextPage, isFetchingNextPage } = useAssistantThread(teamId);
  const ask = useAskAssistant(teamId);
  const clear = useClearThread(teamId);
  const [question, setQuestion] = useState('');
  const messages = data?.pages.flatMap((page) => page.results);

  // A failed question isn't saved, so its text stays in the box. Never retried automatically.
  function submit() {
    ask.mutate(question.trim(), { onSuccess: () => setQuestion('') });
  }

  function confirmClear() {
    Alert.alert('Start a new conversation?', 'This clears your questions and answers for this team.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'New conversation',
        style: 'destructive',
        onPress: () =>
          clear.mutate(undefined, {
            onError: (failure) => Alert.alert("Couldn't clear the conversation", errorMessage(failure)),
          }),
      },
    ]);
  }

  return (
    <KeyboardView>
      <Stack.Screen
        options={{
          title: 'Assistant',
          headerRight: messages?.length
            ? () => (
                <Pressable accessibilityRole="button" onPress={confirmClear} hitSlop={12} disabled={ask.isPending}>
                  <ThemedText type="button" color="link">
                    New conversation
                  </ThemedText>
                </Pressable>
              )
            : undefined,
        }}
      />
      {error ? (
        <View style={styles.padded}>
          <ErrorState error={error} onRetry={() => void refetch()} />
        </View>
      ) : !messages ? (
        <View style={styles.padded}>
          <ListSkeleton />
        </View>
      ) : messages.length === 0 && !ask.isPending ? (
        <View style={styles.padded}>
          <EmptyState
            icon={{ ios: 'sparkles', android: 'smart_toy' }}
            title="Ask about your team's work"
            message="For example: what's overdue, who is busiest, or what changed this week. It only sees what you can see, and it can't change anything."
          />
        </View>
      ) : (
        <FlatList
          inverted
          data={messages}
          keyExtractor={(message) => String(message.id)}
          renderItem={({ item }) => <Turn message={item} />}
          contentContainerStyle={styles.list}
          keyboardShouldPersistTaps="handled"
          onEndReached={() => hasNextPage && !isFetchingNextPage && void fetchNextPage()}
          onEndReachedThreshold={0.5}
          ListHeaderComponent={
            ask.isPending ? (
              <View style={styles.waiting} accessibilityLiveRegion="polite">
                <ActivityIndicator color={t.mutedForeground} />
                <ThemedText type="caption" color="mutedForeground">
                  Thinking. Answers can take up to 25 seconds.
                </ThemedText>
              </View>
            ) : undefined
          }
        />
      )}
      {ask.error ? (
        <View accessibilityRole="alert" style={[styles.note, { backgroundColor: t.tintRose }]}>
          <ThemedText type="caption" color="onTint">
            {askErrorText(ask.error)}
          </ThemedText>
        </View>
      ) : null}
      <Composer
        value={question}
        onChangeText={setQuestion}
        onSend={submit}
        pending={ask.isPending}
        placeholder="Ask a question"
        maxLength={2000}
      />
    </KeyboardView>
  );
}

const styles = StyleSheet.create({
  padded: { flex: 1, padding: Spacing.md },
  list: { padding: Spacing.md, gap: Spacing.sm },
  turn: { borderRadius: Radius.lg, padding: Spacing.sm, gap: 2, maxWidth: '90%', alignSelf: 'flex-start' },
  mine: { alignSelf: 'flex-end' },
  waiting: { flexDirection: 'row', alignItems: 'center', gap: Spacing.xs },
  note: { paddingHorizontal: Spacing.md, paddingVertical: Spacing.xs },
});
