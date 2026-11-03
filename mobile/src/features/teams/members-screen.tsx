import { Stack } from 'expo-router';
import { useState } from 'react';
import { Alert, FlatList, RefreshControl, StyleSheet, View } from 'react-native';

import { ErrorState, ListSkeleton } from '@/components/states';
import { Badge, Button, Card, Chips, FormError, ListRow, SectionTitle, TextField } from '@/components/ui';
import { Spacing } from '@/constants/theme';
import { useMe } from '@/features/auth/query';
import { useSchemaForm } from '@/hooks/use-schema-form';
import { displayName } from '@/lib/format';
import { errorMessage } from '@/lib/http';

import { useAddMember, useChangeMemberRole, useMembers, useRemoveMember, useTeam } from './query';
import { addMemberSchema } from './schema';
import type { Member } from './types';

const ROLE_OPTIONS = [
  { value: 'member', label: 'Member' },
  { value: 'leader', label: 'Leader' },
] as const;

function AddMemberForm({ teamId, onAdded }: { teamId: number; onAdded: () => void }) {
  const add = useAddMember(teamId);
  const { values, set, errors, formError, submitting, handleSubmit } = useSchemaForm(
    addMemberSchema,
    { email: '', role: 'member' },
    async (input) => {
      await add.mutateAsync(input);
      onAdded();
    },
  );

  return (
    <Card>
      <FormError message={formError} />
      <TextField
        label="Add someone by their account's email"
        value={values.email}
        onChangeText={(text) => set('email', text)}
        error={errors.email}
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
      />
      <Chips label="Role" options={ROLE_OPTIONS} value={values.role} onChange={(role) => set('role', role)} />
      <Button label="Add to team" variant="outline" onPress={handleSubmit} loading={submitting} />
    </Card>
  );
}

export function MembersScreen({ teamId }: { teamId: number }) {
  const { team } = useTeam(teamId);
  const { data: me } = useMe();
  const { data: members, error, refetch, isRefetching } = useMembers(teamId);
  const changeRole = useChangeMemberRole(teamId);
  const remove = useRemoveMember(teamId);
  const isLeader = team?.role === 'leader';
  // Remounting the form after each add clears it for the next email.
  const [added, setAdded] = useState(0);

  const onError = (title: string) => (failure: unknown) => Alert.alert(title, errorMessage(failure));

  function manage({ user, role }: Member) {
    const name = user.id === me?.id ? 'yourself' : displayName(user);
    const otherRole = role === 'leader' ? 'member' : 'leader';
    Alert.alert(displayName(user), user.email, [
      {
        text: role === 'leader' ? 'Make a member' : 'Make a leader',
        onPress: () =>
          changeRole.mutate(
            { userId: user.id, role: otherRole },
            { onError: onError("Couldn't change the role") },
          ),
      },
      {
        text: 'Remove from team',
        style: 'destructive',
        onPress: () =>
          Alert.alert(`Remove ${name}?`, 'Their unfinished tasks become unassigned.', [
            { text: 'Cancel', style: 'cancel' },
            {
              text: 'Remove',
              style: 'destructive',
              onPress: () =>
                remove.mutate(user.id, { onError: onError("Couldn't remove them") }),
            },
          ]),
      },
      { text: 'Cancel', style: 'cancel' },
    ]);
  }

  return (
    <FlatList
      data={members}
      keyExtractor={(member) => String(member.user.id)}
      contentInsetAdjustmentBehavior="automatic"
      keyboardShouldPersistTaps="handled"
      contentContainerStyle={styles.list}
      refreshControl={<RefreshControl refreshing={isRefetching} onRefresh={() => void refetch()} />}
      renderItem={({ item }) => (
        <ListRow
          title={displayName(item.user) + (item.user.id === me?.id ? ' (you)' : '')}
          subtitle={item.user.email}
          onPress={isLeader ? () => manage(item) : undefined}
          trailing={<Badge label={item.role === 'leader' ? 'Leader' : 'Member'} tone={item.role === 'leader' ? 'purple' : 'gray'} />}
        />
      )}
      ListHeaderComponent={
        <View style={styles.header}>
          <Stack.Screen options={{ title: 'Members' }} />
          {isLeader ? <AddMemberForm key={added} teamId={teamId} onAdded={() => setAdded((n) => n + 1)} /> : null}
          <SectionTitle>{members ? `${members.length} on the team` : 'Members'}</SectionTitle>
        </View>
      }
      ListEmptyComponent={error ? <ErrorState error={error} onRetry={() => void refetch()} /> : <ListSkeleton />}
    />
  );
}

const styles = StyleSheet.create({
  list: { padding: Spacing.md, gap: Spacing.xs, paddingBottom: Spacing.xxxl },
  header: { gap: Spacing.xs },
});
