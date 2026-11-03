import { useLocalSearchParams } from 'expo-router';

import { AssistantScreen } from '@/features/assistant/assistant-screen';

export default function Route() {
  const { teamId } = useLocalSearchParams<{ teamId: string }>();
  return <AssistantScreen teamId={Number(teamId)} />;
}
