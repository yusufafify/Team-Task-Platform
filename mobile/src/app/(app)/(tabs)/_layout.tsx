import { NativeTabs } from 'expo-router/native-tabs';

import { useUnreadCount } from '@/features/notifications/query';
import { useTheme } from '@/hooks/use-theme';

export default function TabsLayout() {
  const t = useTheme();
  const { data: unread } = useUnreadCount();

  return (
    <NativeTabs tintColor={t.foreground}>
      <NativeTabs.Trigger name="(tasks)">
        <NativeTabs.Trigger.Icon sf="checklist" md="checklist" />
        <NativeTabs.Trigger.Label>Tasks</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="(teams)">
        <NativeTabs.Trigger.Icon sf="person.2" md="group" />
        <NativeTabs.Trigger.Label>Teams</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="(notifications)">
        <NativeTabs.Trigger.Icon sf="bell" md="notifications" />
        <NativeTabs.Trigger.Label>Notifications</NativeTabs.Trigger.Label>
        <NativeTabs.Trigger.Badge hidden={!unread}>{unread && unread > 99 ? '99+' : String(unread ?? '')}</NativeTabs.Trigger.Badge>
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="(account)">
        <NativeTabs.Trigger.Icon sf="person.crop.circle" md="person" />
        <NativeTabs.Trigger.Label>Account</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
