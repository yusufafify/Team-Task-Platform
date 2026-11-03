import { focusManager, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DarkTheme, DefaultTheme, Stack, ThemeProvider } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect, useState } from 'react';
import { AppState, useColorScheme } from 'react-native';

import { Colors } from '@/constants/theme';
import { HttpError } from '@/lib/http';
import { loadTokens, useSessionStatus } from '@/lib/session';

void SplashScreen.preventAutoHideAsync();
void loadTokens();

// TanStack's focus refetch listens to the browser. On a phone, focus is the app coming back.
focusManager.setEventListener((setFocused) => {
  const subscription = AppState.addEventListener('change', (state) => setFocused(state === 'active'));
  return () => subscription.remove();
});

// A 4xx won't change on a retry; network failures and 5xx might.
function shouldRetry(failures: number, error: unknown) {
  return failures < 2 && !(error instanceof HttpError && error.status < 500);
}

export default function RootLayout() {
  const scheme = useColorScheme() === 'dark' ? 'dark' : 'light';
  const base = scheme === 'dark' ? DarkTheme : DefaultTheme;
  const c = Colors[scheme];
  const status = useSessionStatus();
  const [queryClient] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: shouldRetry } } }),
  );

  useEffect(() => {
    if (status === 'loading') return;
    SplashScreen.hide();
    // The next person to sign in on this phone inherits nothing.
    if (status === 'signedOut') queryClient.clear();
  }, [status, queryClient]);

  if (status === 'loading') return null;

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider
        value={{
          ...base,
          colors: {
            ...base.colors,
            primary: c.primary,
            background: c.background,
            card: c.card,
            text: c.foreground,
            border: c.border,
          },
        }}>
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Protected guard={status === 'signedIn'}>
            <Stack.Screen name="(app)" />
          </Stack.Protected>
          <Stack.Protected guard={status === 'signedOut'}>
            <Stack.Screen name="sign-in" />
            <Stack.Screen name="register" />
          </Stack.Protected>
        </Stack>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
