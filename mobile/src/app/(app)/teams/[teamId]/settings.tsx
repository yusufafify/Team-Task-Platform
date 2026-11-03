import { useLocalSearchParams } from 'expo-router';

import { TeamSettingsScreen } from '@/features/teams/team-settings-screen';

export default function Route() {
  const { teamId } = useLocalSearchParams<{ teamId: string }>();
  return <TeamSettingsScreen teamId={Number(teamId)} />;
}
