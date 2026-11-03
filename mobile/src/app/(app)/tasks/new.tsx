import { useLocalSearchParams } from 'expo-router';

import { NewTaskScreen } from '@/features/tasks/task-form-screen';

export default function Route() {
  const { team } = useLocalSearchParams<{ team?: string }>();
  return <NewTaskScreen teamId={team ? Number(team) : undefined} />;
}
