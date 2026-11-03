import { useLocalSearchParams } from 'expo-router';

import { StatsScreen } from '@/features/stats/stats-screen';

export default function Route() {
  const { teamId } = useLocalSearchParams<{ teamId: string }>();
  return <StatsScreen teamId={Number(teamId)} />;
}
