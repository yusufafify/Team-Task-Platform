import { useLocalSearchParams } from 'expo-router';

import { ChatScreen } from '@/features/chat/chat-screen';

export default function Route() {
  const { teamId } = useLocalSearchParams<{ teamId: string }>();
  return <ChatScreen teamId={Number(teamId)} />;
}
