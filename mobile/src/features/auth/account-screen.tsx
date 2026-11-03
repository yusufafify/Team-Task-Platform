import { Alert, StyleSheet, View } from 'react-native';

import { FormScroll } from '@/components/screen';
import { ErrorState, ListSkeleton } from '@/components/states';
import { Button, Card, FormError, SectionTitle, TextField, ThemedText } from '@/components/ui';
import { Spacing } from '@/constants/theme';
import { useSchemaForm } from '@/hooks/use-schema-form';
import { errorMessage } from '@/lib/http';
import type { User } from '@/lib/types';

import { useMe, useSignOut, useSignOutEverywhere, useUpdateProfile } from './query';
import { profileSchema } from './schema';

function ProfileForm({ user }: { user: User }) {
  const update = useUpdateProfile();
  const { values, set, errors, formError, submitting, handleSubmit } = useSchemaForm(
    profileSchema,
    { first_name: user.first_name ?? '', last_name: user.last_name ?? '' },
    (input) => update.mutateAsync(input),
  );
  const changed = values.first_name !== (user.first_name ?? '') || values.last_name !== (user.last_name ?? '');

  return (
    <Card>
      <ThemedText type="caption" color="mutedForeground">
        Signed in as
      </ThemedText>
      <ThemedText type="bodyMd" selectable>
        {user.email}
      </ThemedText>
      <FormError message={formError} />
      <TextField
        label="First name"
        value={values.first_name}
        onChangeText={(text) => set('first_name', text)}
        error={errors.first_name}
        autoComplete="given-name"
      />
      <TextField
        label="Last name"
        value={values.last_name}
        onChangeText={(text) => set('last_name', text)}
        error={errors.last_name}
        autoComplete="family-name"
      />
      <Button label="Save name" variant="outline" onPress={handleSubmit} loading={submitting} disabled={!changed} />
    </Card>
  );
}

export function AccountScreen() {
  const { data: user, error, refetch } = useMe();
  const signOut = useSignOut();
  const everywhere = useSignOutEverywhere();

  function confirmEverywhere() {
    Alert.alert(
      'Sign out everywhere?',
      'This ends your session on every phone and browser. Use it if you think someone else has access.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign out everywhere',
          style: 'destructive',
          onPress: () =>
            everywhere.mutate(undefined, {
              onError: (failure) => Alert.alert("Couldn't sign out everywhere", errorMessage(failure)),
            }),
        },
      ],
    );
  }

  return (
    <FormScroll>
      {error ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : user ? (
        // Remounts after a save, so the fields show the stored, trimmed names.
        <ProfileForm key={`${user.first_name}|${user.last_name}`} user={user} />
      ) : (
        <ListSkeleton rows={2} />
      )}
      <SectionTitle>Sessions</SectionTitle>
      <View style={styles.actions}>
        <Button
          label="Sign out"
          variant="outline"
          onPress={() => signOut.mutate()}
          loading={signOut.isPending}
          disabled={everywhere.isPending}
        />
        <Button
          label="Sign out everywhere"
          variant="ghost"
          onPress={confirmEverywhere}
          loading={everywhere.isPending}
          disabled={signOut.isPending}
        />
      </View>
    </FormScroll>
  );
}

const styles = StyleSheet.create({
  actions: { gap: Spacing.xs },
});
