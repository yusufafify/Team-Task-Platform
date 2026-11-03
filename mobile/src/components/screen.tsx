import { useHeaderHeight } from 'expo-router/react-navigation';
import type { ReactNode } from 'react';
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Pressable,
  ScrollView,
  StyleSheet,
  TextInput,
  View,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Icon } from '@/components/ui';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

// Android draws edge to edge, so the window no longer resizes for the keyboard on either platform.
export function KeyboardView({ children }: { children: ReactNode }) {
  const headerHeight = useHeaderHeight();
  const t = useTheme();
  return (
    <KeyboardAvoidingView
      behavior="padding"
      keyboardVerticalOffset={headerHeight}
      style={[styles.flex, { backgroundColor: t.background }]}>
      {children}
    </KeyboardAvoidingView>
  );
}

export function FormScroll({ children }: { children: ReactNode }) {
  return (
    <KeyboardView>
      <ScrollView
        contentInsetAdjustmentBehavior="automatic"
        keyboardShouldPersistTaps="handled"
        contentContainerStyle={styles.form}>
        {children}
      </ScrollView>
    </KeyboardView>
  );
}

interface ComposerProps {
  value: string;
  onChangeText: (text: string) => void;
  onSend: () => void;
  placeholder: string;
  pending?: boolean;
  maxLength: number;
}

export function Composer({ value, onChangeText, onSend, placeholder, pending, maxLength }: ComposerProps) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const canSend = value.trim().length > 0 && !pending;

  return (
    <View
      style={[
        styles.composer,
        { borderColor: t.border, backgroundColor: t.background, paddingBottom: Math.max(insets.bottom, Spacing.xs) },
      ]}>
      <TextInput
        accessibilityLabel={placeholder}
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        placeholderTextColor={t.steel}
        maxLength={maxLength}
        multiline
        style={[styles.input, { color: t.foreground, borderColor: t.input }]}
      />
      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Send"
        accessibilityState={{ disabled: !canSend, busy: pending }}
        disabled={!canSend}
        onPress={onSend}
        style={({ pressed }) => [
          styles.send,
          { backgroundColor: pressed ? t.primaryPressed : t.primary },
          !canSend && styles.disabled,
        ]}>
        {pending ? (
          <ActivityIndicator color={t.primaryForeground} />
        ) : (
          <Icon name={{ ios: 'arrow.up', android: 'send' }} size={18} color="primaryForeground" />
        )}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  form: { padding: Spacing.md, gap: Spacing.md, paddingBottom: Spacing.xxxl },
  composer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: Spacing.xs,
    paddingHorizontal: Spacing.md,
    paddingTop: Spacing.xs,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 140,
    borderWidth: 1,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.sm,
    paddingTop: 11,
    paddingBottom: 11,
    fontSize: 16,
  },
  send: { width: 44, height: 44, borderRadius: Radius.md, alignItems: 'center', justifyContent: 'center' },
  disabled: { opacity: 0.5 },
});
