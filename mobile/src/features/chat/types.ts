import type { User } from '@/lib/types';

export interface Message {
  id: number;
  team: number;
  author: User;
  body: string;
  created_at: string;
}
