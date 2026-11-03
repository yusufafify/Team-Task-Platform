import { router, Stack } from 'expo-router';
import { FlatList, RefreshControl, StyleSheet, View } from 'react-native';

import { FormScroll } from '@/components/screen';
import { EmptyState, ErrorState, ListSkeleton } from '@/components/states';
import { Badge, Button, FormError, ListRow, TextField } from '@/components/ui';
import { Spacing } from '@/constants/theme';
import { useSchemaForm } from '@/hooks/use-schema-form';

import { useCreateTeam, useTeams } from './query';
import { teamSchema } from './schema';

export function TeamsScreen() {
  const { data: teams, error, refetch, isRefetching } = useTeams();

  return (
    <FlatList
      data={teams}
      keyExtractor={(team) => String(team.id)}
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={styles.list}
      refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={() => void refetch()} />}
      renderItem={({ item }) => (
        <ListRow
          title={item.name}
          icon={{ ios: 'person.2', android: 'group' }}
          onPress={() => router.push(`/teams/${item.id}`)}
          trailing={<Badge label={item.role === 'leader' ? 'Leader' : 'Member'} tone={item.role === 'leader' ? 'purple' : 'gray'} />}
        />
      )}
      ListHeaderComponent={
        teams?.length ? (
          <View style={styles.header}>
            <Button label="New team" variant="outline" onPress={() => router.push('/teams/new')} />
          </View>
        ) : undefined
      }
      ListEmptyComponent={
        error ? (
          <ErrorState error={error} onRetry={() => void refetch()} />
        ) : !teams ? (
          <ListSkeleton />
        ) : (
          <EmptyState
            icon={{ ios: 'person.2', android: 'group' }}
            title="You're not on a team yet"
            message="Create a team to lead it, or ask a leader to add you by your account's email."
            action={<Button label="Create a team" onPress={() => router.push('/teams/new')} />}
          />
        )
      }
    />
  );
}

export function deviceTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Africa/Cairo';
}

export function NewTeamScreen() {
  const create = useCreateTeam();
  const { values, set, errors, formError, submitting, handleSubmit } = useSchemaForm(
    teamSchema,
    { name: '', timezone: deviceTimezone() },
    async (input) => {
      const team = await create.mutateAsync(input);
      router.replace(`/teams/${team.id}`);
    },
  );

  return (
    <FormScroll>
      <Stack.Screen options={{ title: 'New team' }} />
      <FormError message={formError} />
      <TextField
        label="Team name"
        value={values.name}
        onChangeText={(text) => set('name', text)}
        error={errors.name}
        maxLength={150}
        autoFocus
      />
      <TextField
        label="Timezone"
        value={values.timezone}
        onChangeText={(text) => set('timezone', text)}
        error={errors.timezone}
        autoCapitalize="none"
        autoCorrect={false}
      />
      <Button label="Create team" onPress={handleSubmit} loading={submitting} />
    </FormScroll>
  );
}

const styles = StyleSheet.create({
  list: { padding: Spacing.md, gap: Spacing.xs, paddingBottom: Spacing.xxxl },
  header: { marginBottom: Spacing.xs },
});
