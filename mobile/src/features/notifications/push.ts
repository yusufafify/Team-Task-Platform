import Constants from 'expo-constants';
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import { AndroidImportance } from 'expo-notifications';
import { Platform } from 'react-native';
import { z } from 'zod';

import { http } from '@/lib/http';

// Pushes come from outside the app, so their data is checked before it picks a screen.
export const pushDataSchema = z.object({
  notification: z.number(),
  kind: z.string(),
  task: z.number().nullable(),
});

Notifications.setNotificationHandler({
  // The socket already updates the list in the foreground; the banner is the nudge.
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: false,
    shouldSetBadge: false,
  }),
});

let registered: string | null = null;

// Called after every sign-in and app start, because the server drops tokens Expo calls dead.
export async function registerPushToken(): Promise<void> {
  const projectId: unknown = Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;
  // shortcut: no push until the app is linked to an EAS project (`eas init`) and runs on a real
  // device in a development build; Expo Go and simulators can't get a push token.
  if (!Device.isDevice || typeof projectId !== 'string') return;

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Notifications',
      importance: AndroidImportance.DEFAULT,
    });
  }
  let { status } = await Notifications.getPermissionsAsync();
  if (status !== 'granted') ({ status } = await Notifications.requestPermissionsAsync());
  if (status !== 'granted') return;

  const { data: token } = await Notifications.getExpoPushTokenAsync({ projectId });
  await http.post('device-tokens/', { token });
  registered = token;
}

export async function unregisterPushToken(): Promise<void> {
  if (!registered) return;
  await http.delete(`device-tokens/${encodeURIComponent(registered)}/`).catch(() => undefined);
  registered = null;
}
