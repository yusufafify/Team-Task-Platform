import { SymbolView, type SymbolViewProps } from 'expo-symbols';
import type { ReactNode } from 'react';
import {
  ActivityIndicator,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
  type TextProps,
  type ViewProps,
} from 'react-native';

import { Radius, Spacing, Type, type Theme } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export type IconName = SymbolViewProps['name'];

interface ThemedTextProps extends TextProps {
  type?: keyof typeof Type;
  color?: keyof Theme;
}

export function ThemedText({ type = 'bodyMd', color = 'foreground', style, ...props }: ThemedTextProps) {
  const t = useTheme();
  return <Text style={[Type[type], { color: t[color] }, style]} {...props} />;
}

export function Icon({ name, size = 20, color = 'foreground' }: { name: IconName; size?: number; color?: keyof Theme }) {
  const t = useTheme();
  return <SymbolView name={name} size={size} tintColor={t[color]} />;
}

type Variant = 'primary' | 'outline' | 'ghost' | 'destructive';

interface ButtonProps {
  label: string;
  onPress: () => void;
  variant?: Variant;
  disabled?: boolean;
  loading?: boolean;
}

export function Button({ label, onPress, variant = 'primary', disabled, loading }: ButtonProps) {
  const t = useTheme();
  const look = {
    primary: { fill: t.primary, pressed: t.primaryPressed, text: t.primaryForeground, border: t.primary },
    outline: { fill: t.background, pressed: t.muted, text: t.foreground, border: t.borderStrong },
    ghost: { fill: 'transparent', pressed: t.muted, text: t.foreground, border: 'transparent' },
    destructive: { fill: t.destructive, pressed: t.destructive, text: t.destructiveForeground, border: t.destructive },
  }[variant];

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: disabled || loading, busy: loading }}
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: pressed ? look.pressed : look.fill, borderColor: look.border },
        (disabled || loading) && styles.disabled,
      ]}>
      {loading ? (
        <ActivityIndicator color={look.text} />
      ) : (
        <Text style={[Type.button, { color: look.text }]}>{label}</Text>
      )}
    </Pressable>
  );
}

interface FieldProps extends TextInputProps {
  label: string;
  error?: string;
}

export function TextField({ label, error, style, ...input }: FieldProps) {
  const t = useTheme();
  return (
    <View style={styles.field}>
      <ThemedText type="captionBold">{label}</ThemedText>
      <TextInput
        accessibilityLabel={label}
        placeholderTextColor={t.steel}
        style={[
          styles.input,
          input.multiline && styles.multiline,
          { color: t.foreground, borderColor: error ? t.destructive : t.input, backgroundColor: t.background },
          style,
        ]}
        {...input}
      />
      {error ? (
        <ThemedText type="caption" color="destructiveText">
          {error}
        </ThemedText>
      ) : null}
    </View>
  );
}

export function FormError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <ThemedText type="bodySm" color="destructiveText" accessibilityRole="alert">
      {message}
    </ThemedText>
  );
}

export type Tone = 'purple' | 'orange' | 'green' | 'gray' | 'red';

export function Badge({ label, tone = 'gray' }: { label: string; tone?: Tone }) {
  const t = useTheme();
  const [fill, text] = {
    purple: [t.tintLavender, t.tagPurple],
    orange: [t.tintPeach, t.tagOrange],
    green: [t.tintMint, t.tagGreen],
    gray: [t.tintGray, t.onTint],
    red: [t.tintRose, t.destructiveText],
  }[tone];
  return (
    <View style={[styles.badge, { backgroundColor: fill }]}>
      <Text style={[Type.captionBold, { color: text }]}>{label}</Text>
    </View>
  );
}

export function Card({ style, ...props }: ViewProps) {
  const t = useTheme();
  return <View style={[styles.card, { backgroundColor: t.card, borderColor: t.border }, style]} {...props} />;
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <ThemedText type="microUppercase" color="mutedForeground" accessibilityRole="header" style={styles.sectionTitle}>
      {children}
    </ThemedText>
  );
}

interface ChipsProps<T> {
  label?: string;
  options: readonly { value: T; label: string }[];
  value: T;
  onChange: (value: T) => void;
  disabled?: boolean;
}

// Pill choices for short fixed sets: status, priority, role, and a team's members.
export function Chips<T>({ label, options, value, onChange, disabled }: ChipsProps<T>) {
  const t = useTheme();
  return (
    <View style={styles.field}>
      {label ? <ThemedText type="captionBold">{label}</ThemedText> : null}
      <View style={styles.chips} accessibilityRole="radiogroup" accessibilityLabel={label}>
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <Pressable
              key={String(option.value)}
              accessibilityRole="radio"
              accessibilityState={{ checked: selected, disabled }}
              disabled={disabled}
              onPress={() => onChange(option.value)}
              hitSlop={4}
              style={({ pressed }) => [
                styles.chip,
                {
                  backgroundColor: selected ? t.inverse : pressed ? t.muted : t.background,
                  borderColor: selected ? t.inverse : t.borderStrong,
                },
                disabled && styles.disabled,
              ]}>
              <Text style={[Type.caption, { color: selected ? t.inverseForeground : t.foreground }]}>
                {option.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

interface ListRowProps {
  title: string;
  subtitle?: string;
  icon?: IconName;
  onPress?: () => void;
  trailing?: ReactNode;
}

export function ListRow({ title, subtitle, icon, onPress, trailing }: ListRowProps) {
  const t = useTheme();
  return (
    <Pressable
      accessibilityRole={onPress ? 'button' : undefined}
      disabled={!onPress}
      onPress={onPress}
      style={({ pressed }) => [styles.row, { backgroundColor: pressed ? t.muted : t.card, borderColor: t.border }]}>
      {icon ? (
        <View style={[styles.rowIcon, { backgroundColor: t.secondary }]}>
          <Icon name={icon} size={18} color="charcoal" />
        </View>
      ) : null}
      <View style={styles.rowText}>
        <ThemedText type="bodyMd" numberOfLines={1}>
          {title}
        </ThemedText>
        {subtitle ? (
          <ThemedText type="caption" color="mutedForeground" numberOfLines={2}>
            {subtitle}
          </ThemedText>
        ) : null}
      </View>
      {trailing}
      {onPress ? <Icon name={{ ios: 'chevron.right', android: 'chevron_right' }} size={14} color="steel" /> : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: 44,
    paddingHorizontal: Spacing.md,
    borderRadius: Radius.md,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  disabled: { opacity: 0.5 },
  field: { gap: Spacing.xxs + 2 },
  input: {
    minHeight: 44,
    borderWidth: 1,
    borderRadius: Radius.md,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    fontSize: 16,
  },
  multiline: { minHeight: 96, textAlignVertical: 'top' },
  badge: {
    alignSelf: 'flex-start',
    borderRadius: Radius.sm,
    paddingHorizontal: Spacing.xs,
    paddingVertical: 2,
  },
  card: { borderWidth: 1, borderRadius: Radius.lg, padding: Spacing.md, gap: Spacing.xs },
  sectionTitle: { marginTop: Spacing.md },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.xs },
  chip: {
    minHeight: 36,
    justifyContent: 'center',
    paddingHorizontal: Spacing.sm,
    borderRadius: Radius.full,
    borderWidth: 1,
  },
  row: {
    minHeight: 56,
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderWidth: 1,
    borderRadius: Radius.lg,
  },
  rowIcon: {
    width: 32,
    height: 32,
    borderRadius: Radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rowText: { flex: 1, gap: 2 },
});
