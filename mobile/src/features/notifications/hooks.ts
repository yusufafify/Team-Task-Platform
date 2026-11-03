import { useQueryClient } from '@tanstack/react-query';
import * as Notifications from 'expo-notifications';
import { router, usePathname } from 'expo-router';
import { useEffect } from 'react';

import { teamsQuery } from '@/features/teams/query';

import { pushDataSchema, registerPushToken } from './push';
import { markRead, NOTIFICATIONS_KEY, unreadCountQuery } from './query';
import type { Notification } from './types';

type Opened = Pick<Notification, 'id' | 'kind' | 'task' | 'body'>;

// Shared by a tap in the list and a tap on a push, which carries the same fields.
export function useOpenNotification() {
  const queryClient = useQueryClient();

  return async ({ id, kind, task, body }: Opened) => {
    markRead(id)
      .then(() => queryClient.invalidateQueries({ queryKey: NOTIFICATIONS_KEY }))
      .catch(() => undefined);

    if (task !== null) return router.push(`/tasks/${task}`);
    if (kind === 'report_ready') {
      // It carries no team id, so the team is the one led whose name starts the body.
      const teams = await queryClient.fetchQuery(teamsQuery).catch(() => []);
      const team = teams
        .filter(({ role, name }) => role === 'leader' && body.startsWith(`${name}: `))
        .sort((a, b) => b.name.length - a.name.length)[0];
      return router.push(team ? `/teams/${team.id}/reports` : '/teams');
    }
    // A kind this version doesn't know: the list is the record.
    router.navigate('/notifications');
  };
}

// Module-level, so signing out and back in doesn't replay the tap that opened the app.
let handledPush: string | null = null;

export function usePushSetup() {
  const open = useOpenNotification();
  const response = Notifications.useLastNotificationResponse();

  useEffect(() => {
    void registerPushToken().catch(() => undefined);
    const subscription = Notifications.addPushTokenListener(() => void registerPushToken().catch(() => undefined));
    return () => subscription.remove();
  }, []);

  useEffect(() => {
    if (!response || response.actionIdentifier !== Notifications.DEFAULT_ACTION_IDENTIFIER) return;
    const { identifier, content } = response.notification.request;
    if (handledPush === identifier) return;
    handledPush = identifier;
    const data = pushDataSchema.safeParse(content.data);
    if (data.success) {
      void open({ id: data.data.notification, kind: data.data.kind, task: data.data.task, body: content.body ?? '' });
    }
  }, [response, open]);
}

// The overview asks for the unread count on open, focus and every screen change, with no timer.
export function useUnreadCheckOnNavigate() {
  const queryClient = useQueryClient();
  const pathname = usePathname();
  useEffect(() => {
    void queryClient.invalidateQueries({ queryKey: unreadCountQuery.queryKey });
  }, [pathname, queryClient]);
}
