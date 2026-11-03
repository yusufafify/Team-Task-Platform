import { Stack } from 'expo-router';

export default function Layout() {
  return (
    <Stack>
      <Stack.Screen name="teams" options={{ title: 'Teams', headerLargeTitleEnabled: true }} />
    </Stack>
  );
}
