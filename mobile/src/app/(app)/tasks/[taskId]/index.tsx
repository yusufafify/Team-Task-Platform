import { useLocalSearchParams } from 'expo-router';

import { TaskScreen } from '@/features/tasks/task-screen';

export default function Route() {
  const { taskId } = useLocalSearchParams<{ taskId: string }>();
  return <TaskScreen taskId={Number(taskId)} />;
}
