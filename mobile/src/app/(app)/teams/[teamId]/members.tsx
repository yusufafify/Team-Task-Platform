import { useLocalSearchParams } from 'expo-router';

import { MembersScreen } from '@/features/teams/members-screen';

export default function Route() {
  const { teamId } = useLocalSearchParams<{ teamId: string }>();
  return <MembersScreen teamId={Number(teamId)} />;
}
