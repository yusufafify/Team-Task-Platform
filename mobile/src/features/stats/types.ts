import type { User } from '@/lib/types';

export interface StatsPeriod {
  start: string;
  end: string;
}

export interface Stats {
  due: number;
  completed: number;
  on_time: number;
  delayed: number;
  overdue: number;
  completion_rate: number | null;
  on_time_rate: number | null;
  average_delay_days: number | null;
}

export interface TeamStats {
  start: string;
  end: string;
  timezone: string;
  scope: 'team' | 'self';
  stats: Stats;
  members: { user: User; stats: Stats }[];
}
