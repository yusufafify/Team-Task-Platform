import { useLocalSearchParams } from 'expo-router';

import { ReportsScreen } from '@/features/reports/reports-screen';

export default function Route() {
  const { teamId } = useLocalSearchParams<{ teamId: string }>();
  return <ReportsScreen teamId={Number(teamId)} />;
}
