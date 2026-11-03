import type { Message } from '@/features/chat/types';
import type { Notification } from '@/features/notifications/types';

export type LiveEvent = { type: 'message'; data: Message } | { type: 'notification'; data: Notification };
