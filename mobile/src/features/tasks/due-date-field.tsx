import { DateTimePicker } from '@expo/ui/community/datetime-picker';
import { useState } from 'react';
import { Platform, StyleSheet, useColorScheme, View } from 'react-native';

import { Button, ThemedText } from '@/components/ui';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';
import { formatDate, formatTime } from '@/lib/format';

interface DueDateFieldProps {
  value: Date;
  onChange: (date: Date) => void;
  error?: string;
}

// iOS has a compact date-and-time control. Android has no inline one, so it opens a dialog per part.
export function DueDateField({ value, onChange, error }: DueDateFieldProps) {
  const t = useTheme();
  const scheme = useColorScheme() === 'dark' ? 'dark' : 'light';
  const [open, setOpen] = useState<'date' | 'time' | null>(null);

  return (
    <View style={styles.field}>
      <ThemedText type="captionBold">Due</ThemedText>
      {Platform.OS === 'ios' ? (
        <View style={styles.row}>
          <DateTimePicker
            mode="datetime"
            display="compact"
            value={value}
            accentColor={t.primary}
            themeVariant={scheme}
            onValueChange={(_event, date) => onChange(date)}
          />
        </View>
      ) : (
        <View style={styles.row}>
          <Button label={formatDate(value.toISOString())} variant="outline" onPress={() => setOpen('date')} />
          <Button label={formatTime(value.toISOString())} variant="outline" onPress={() => setOpen('time')} />
        </View>
      )}
      {open ? (
        <DateTimePicker
          mode={open}
          value={value}
          is24Hour
          accentColor={t.primary}
          themeVariant={scheme}
          onChange={(event, date) => {
            setOpen(null);
            if (event.type === 'set' && date) onChange(date);
          }}
        />
      ) : null}
      {error ? (
        <ThemedText type="caption" color="destructiveText">
          {error}
        </ThemedText>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  field: { gap: Spacing.xxs + 2 },
  row: { flexDirection: 'row', gap: Spacing.xs, alignItems: 'center' },
});
