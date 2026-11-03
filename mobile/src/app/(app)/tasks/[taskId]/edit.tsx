import { useLocalSearchParams } from 'expo-router';

import { EditTaskScreen } from '@/features/tasks/task-form-screen';

export default function Route() {
  const { taskId } = useLocalSearchParams<{ taskId: string }>();
  return <EditTaskScreen taskId={Number(taskId)} />;
}
