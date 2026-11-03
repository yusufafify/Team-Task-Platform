import { router, Stack } from 'expo-router';
import { Alert } from 'react-native';

import { FormScroll } from '@/components/screen';
import { ErrorState, ListSkeleton } from '@/components/states';
import { Button, Card, FormError, SectionTitle, TextField, ThemedText } from '@/components/ui';
import { useSchemaForm } from '@/hooks/use-schema-form';
import { errorMessage } from '@/lib/http';

import { useDeleteTeam, useTeam, useUpdateTeam } from './query';
import { teamSchema } from './schema';
import { deviceTimezone } from './teams-screen';
import type { Team } from './types';

function SettingsForm({ team }: { team: Team }) {
  const update = useUpdateTeam(team.id);
  const remove = useDeleteTeam(team.id);
  const { values, set, errors, formError, submitting, handleSubmit } = useSchemaForm(
    teamSchema,
    { name: team.name, timezone: team.timezone ?? deviceTimezone() },
    (input) => update.mutateAsync(input),
  );

  function confirmDelete() {
    Alert.alert(`Delete ${team.name}?`, 'Only a team with no tasks or messages can be deleted.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete team',
        style: 'destructive',
        onPress: () =>
          remove.mutate(undefined, {
            onSuccess: () => router.dismissTo('/teams'),
            onError: (failure) => Alert.alert("Couldn't delete the team", errorMessage(failure)),
          }),
      },
    ]);
  }

  return (
    <>
      <FormError message={formError} />
      <TextField
        label="Team name"
        value={values.name}
        onChangeText={(text) => set('name', text)}
        error={errors.name}
        maxLength={150}
      />
      <TextField
        label="Timezone"
        value={values.timezone}
        onChangeText={(text) => set('timezone', text)}
        error={errors.timezone}
        autoCapitalize="none"
        autoCorrect={false}
      />
      <ThemedText type="caption" color="mutedForeground">
        Stats count whole days in this timezone.
      </ThemedText>
      <Button label="Save changes" onPress={handleSubmit} loading={submitting} />
      <SectionTitle>Danger zone</SectionTitle>
      <Card>
        <ThemedText type="bodySm" color="mutedForeground">
          Deleting is only possible before the team has any tasks or messages.
        </ThemedText>
        <Button label="Delete team" variant="destructive" onPress={confirmDelete} loading={remove.isPending} />
      </Card>
    </>
  );
}

export function TeamSettingsScreen({ teamId }: { teamId: number }) {
  const { team, error, refetch } = useTeam(teamId);
  return (
    <FormScroll>
      <Stack.Screen options={{ title: 'Team settings' }} />
      {error ? <ErrorState error={error} onRetry={() => void refetch()} /> : team ? <SettingsForm team={team} /> : <ListSkeleton rows={2} />}
    </FormScroll>
  );
}
