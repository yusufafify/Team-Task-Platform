import { Stack } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { useLiveSocket } from '@/features/live/hooks';
import { usePushSetup, useUnreadCheckOnNavigate } from '@/features/notifications/hooks';

// Everything here runs only while signed in: the one socket, push, and the unread checks.
export default function AppLayout() {
  const { noteInput } = useLiveSocket();
  usePushSetup();
  useUnreadCheckOnNavigate();

  return (
    // Touches count as the "input" that keeps the socket's fallback polling alive.
    <View style={styles.flex} onTouchStart={noteInput}>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      </Stack>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
});
