import { useLocalSearchParams } from 'expo-router';

import { TeamScreen } from '@/features/teams/team-screen';

export default function Route() {
  const { teamId } = useLocalSearchParams<{ teamId: string }>();
  return <TeamScreen teamId={Number(teamId)} />;
}
