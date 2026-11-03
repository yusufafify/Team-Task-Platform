import { router, Stack, type Href } from 'expo-router';
import { StyleSheet, View } from 'react-native';

import { ErrorState, ListSkeleton } from '@/components/states';
import { Button, ListRow, SectionTitle, type IconName } from '@/components/ui';
import { Spacing } from '@/constants/theme';
import { TaskList } from '@/features/tasks/task-list';

import { useTeam } from './query';
import type { Team } from './types';

interface Section {
  title: string;
  subtitle: string;
  icon: IconName;
  href: Href;
  leadersOnly?: boolean;
}

function sections(team: Team): Section[] {
  const base = `/teams/${team.id}` as const;
  return [
    { title: 'Chat', subtitle: 'Talk with the whole team', icon: { ios: 'bubble.left.and.bubble.right', android: 'forum' }, href: `${base}/chat` },
    { title: 'Assistant', subtitle: 'Ask about the team’s work', icon: { ios: 'sparkles', android: 'smart_toy' }, href: `${base}/assistant` },
    { title: 'Stats', subtitle: team.role === 'leader' ? 'Team and member numbers' : 'Your numbers', icon: { ios: 'chart.bar', android: 'bar_chart' }, href: `${base}/stats` },
    { title: 'Reports', subtitle: 'Monthly summaries', icon: { ios: 'doc.text', android: 'description' }, href: `${base}/reports`, leadersOnly: true },
    { title: 'Members', subtitle: 'Who is on the team', icon: { ios: 'person.2', android: 'group' }, href: `${base}/members` },
    { title: 'Settings', subtitle: 'Name, timezone and deletion', icon: { ios: 'gearshape', android: 'settings' }, href: `${base}/settings`, leadersOnly: true },
  ];
}

function TeamHeader({ team }: { team: Team }) {
  const isLeader = team.role === 'leader';
  return (
    <View style={styles.header}>
      {sections(team)
        .filter(({ leadersOnly }) => isLeader || !leadersOnly)
        .map(({ title, subtitle, icon, href }) => (
          <ListRow key={title} title={title} subtitle={subtitle} icon={icon} onPress={() => router.push(href)} />
        ))}
      <SectionTitle>{isLeader ? 'Team tasks' : 'Your tasks here'}</SectionTitle>
      {isLeader ? (
        <Button label="New task" variant="outline" onPress={() => router.push({ pathname: '/tasks/new', params: { team: String(team.id) } })}
        />
      ) : null}
    </View>
  );
}

export function TeamScreen({ teamId }: { teamId: number }) {
  const { team, error, refetch, isPending } = useTeam(teamId);

  if (!team) {
    return (
      <View style={styles.missing}>
        <Stack.Screen options={{ title: 'Team' }} />
        {isPending ? (
          <ListSkeleton />
        ) : (
          // The list loaded without this team, so it's gone or this person was removed.
          <ErrorState error={error ?? new Error('You are no longer on this team.')} onRetry={() => void refetch()} />
        )}
      </View>
    );
  }

  return (
    <>
      <Stack.Screen options={{ title: team.name }} />
      <TaskList team={team.id} header={<TeamHeader team={team} />} />
    </>
  );
}

const styles = StyleSheet.create({
  header: { gap: Spacing.xs },
  missing: { padding: Spacing.md },
});
