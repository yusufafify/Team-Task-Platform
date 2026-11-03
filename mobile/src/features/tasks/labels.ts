import type { Tone } from '@/components/ui';

import type { TaskPriority, TaskStatus } from './types';

export const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'To do',
  in_progress: 'In progress',
  blocked: 'Blocked',
  done: 'Done',
};

export const STATUS_TONES: Record<TaskStatus, Tone> = {
  todo: 'gray',
  in_progress: 'purple',
  blocked: 'orange',
  done: 'green',
};

export const PRIORITY_LABELS: Record<TaskPriority, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High',
  urgent: 'Urgent',
};

export const PRIORITY_TONES: Record<TaskPriority, Tone> = {
  low: 'gray',
  medium: 'purple',
  high: 'orange',
  urgent: 'red',
};

export const STATUS_OPTIONS = Object.entries(STATUS_LABELS).map(([value, label]) => ({
  value: value as TaskStatus,
  label,
}));

export const PRIORITY_OPTIONS = Object.entries(PRIORITY_LABELS).map(([value, label]) => ({
  value: value as TaskPriority,
  label,
}));
