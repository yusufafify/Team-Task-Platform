import { StatusBar } from 'expo-status-bar';
import { Link } from 'expo-router';
import type { ReactNode } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { KeyboardView } from '@/components/screen';
import { Button, FormError, TextField, ThemedText } from '@/components/ui';
import { Brand, Spacing, Type } from '@/constants/theme';

import { useLoginForm, useRegisterForm } from './hooks';

function AuthLayout({ title, lead, children }: { title: string; lead: string; children: ReactNode }) {
  const insets = useSafeAreaInsets();
  return (
    <KeyboardView>
      <StatusBar style="light" />
      <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.scroll}>
        <View style={[styles.band, { paddingTop: insets.top + Spacing.xxl }]}>
          <Text style={[Type.microUppercase, { color: Brand.onDarkMuted }]}>Nesma Airlines</Text>
          <Text accessibilityRole="header" style={[Type.heading3, { color: Brand.onDark }]}>
            {title}
          </Text>
          <Text style={[Type.bodyMd, { color: Brand.onDarkMuted }]}>{lead}</Text>
        </View>
        <View style={[styles.form, { paddingBottom: insets.bottom + Spacing.xl }]}>{children}</View>
      </ScrollView>
    </KeyboardView>
  );
}

export function SignInScreen() {
  const { values, set, errors, formError, submitting, handleSubmit } = useLoginForm();
  return (
    <AuthLayout title="Sign in" lead="Pick up your team's tasks, chat and reports where you left them.">
      <FormError message={formError} />
      <TextField
        label="Email"
        value={values.email}
        onChangeText={(text) => set('email', text)}
        error={errors.email}
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
        textContentType="emailAddress"
        returnKeyType="next"
      />
      <TextField
        label="Password"
        value={values.password}
        onChangeText={(text) => set('password', text)}
        error={errors.password}
        secureTextEntry
        autoComplete="current-password"
        textContentType="password"
        returnKeyType="go"
        onSubmitEditing={handleSubmit}
      />
      <Button label="Sign in" onPress={handleSubmit} loading={submitting} />
      <View style={styles.switch}>
        <ThemedText type="bodySm" color="mutedForeground">
          New here?
        </ThemedText>
        <Link href="/register" replace>
          <ThemedText type="bodySm" color="link">
            Create an account
          </ThemedText>
        </Link>
      </View>
    </AuthLayout>
  );
}

export function RegisterScreen() {
  const { values, set, errors, formError, submitting, handleSubmit } = useRegisterForm();
  return (
    <AuthLayout title="Create your account" lead="A team leader can add you to their team by this email.">
      <FormError message={formError} />
      <View style={styles.names}>
        <View style={styles.name}>
          <TextField
            label="First name"
            value={values.first_name}
            onChangeText={(text) => set('first_name', text)}
            error={errors.first_name}
            autoComplete="given-name"
            textContentType="givenName"
          />
        </View>
        <View style={styles.name}>
          <TextField
            label="Last name"
            value={values.last_name}
            onChangeText={(text) => set('last_name', text)}
            error={errors.last_name}
            autoComplete="family-name"
            textContentType="familyName"
          />
        </View>
      </View>
      <TextField
        label="Email"
        value={values.email}
        onChangeText={(text) => set('email', text)}
        error={errors.email}
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
        textContentType="emailAddress"
      />
      <TextField
        label="Password"
        value={values.password}
        onChangeText={(text) => set('password', text)}
        error={errors.password}
        secureTextEntry
        autoComplete="new-password"
        textContentType="newPassword"
        onSubmitEditing={handleSubmit}
      />
      <Button label="Create account" onPress={handleSubmit} loading={submitting} />
      <View style={styles.switch}>
        <ThemedText type="bodySm" color="mutedForeground">
          Already have an account?
        </ThemedText>
        <Link href="/sign-in" replace>
          <ThemedText type="bodySm" color="link">
            Sign in
          </ThemedText>
        </Link>
      </View>
    </AuthLayout>
  );
}

const styles = StyleSheet.create({
  scroll: { flexGrow: 1 },
  band: {
    backgroundColor: Brand.navy,
    paddingHorizontal: Spacing.xl,
    paddingBottom: Spacing.xxl,
    gap: Spacing.xs,
  },
  form: { padding: Spacing.xl, gap: Spacing.md },
  switch: { flexDirection: 'row', justifyContent: 'center', gap: Spacing.xxs, paddingVertical: Spacing.xs },
  names: { flexDirection: 'row', gap: Spacing.sm },
  name: { flex: 1 },
});
