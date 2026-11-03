import { Field } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import type { Team } from './types'

const DEFAULT_TIMEZONE = 'Africa/Cairo'

interface TeamFieldsProps {
  team?: Team
  errors: Record<string, string>
}

export function TeamFields({ team, errors }: TeamFieldsProps) {
  const timezone = team?.timezone ?? DEFAULT_TIMEZONE
  const zones = [...new Set([timezone, ...Intl.supportedValuesOf('timeZone')])]

  return (
    <>
      <Field label="Team name" error={errors.name}>
        <Input name="name" defaultValue={team?.name} maxLength={150} required />
      </Field>
      <Field
        label="Time zone"
        error={errors.timezone}
        hint="Stats and reports count whole days in this time zone."
      >
        <Select name="timezone" defaultValue={timezone}>
          {zones.map((zone) => (
            <option key={zone}>{zone}</option>
          ))}
        </Select>
      </Field>
    </>
  )
}
