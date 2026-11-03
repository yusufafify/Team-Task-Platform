import { Stack } from 'expo-router';

export default function Layout() {
  return (
    <Stack>
      <Stack.Screen name="notifications" options={{ title: 'Notifications', headerLargeTitleEnabled: true }} />
    </Stack>
  );
}
