import type { User } from '@/types/api'

const LOCALE = 'en-GB'
const DAY_MS = 86_400_000

const timeFormat = new Intl.DateTimeFormat(LOCALE, {
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})
const dayFormat = new Intl.DateTimeFormat(LOCALE, {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
})
const fullDayFormat = new Intl.DateTimeFormat(LOCALE, {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})
// Report months are date-only strings, so reading them in UTC keeps them on the first of the month.
const monthFormat = new Intl.DateTimeFormat(LOCALE, {
  month: 'long',
  year: 'numeric',
  timeZone: 'UTC',
})

export function displayName(user: User): string {
  return (
    [user.first_name, user.last_name].filter(Boolean).join(' ') || user.email
  )
}

export function formatDay(iso: string, now = new Date()): string {
  const date = new Date(iso)
  const today = new Date(now).setHours(0, 0, 0, 0)
  const offset = Math.round(
    (new Date(date).setHours(0, 0, 0, 0) - today) / DAY_MS,
  )
  if (offset === 0) return 'Today'
  if (offset === 1) return 'Tomorrow'
  if (offset === -1) return 'Yesterday'
  return dayFormat.format(date)
}

export function formatTime(iso: string): string {
  return timeFormat.format(new Date(iso))
}

export function formatDayTime(iso: string): string {
  return `${formatDay(iso)} ${formatTime(iso)}`
}

export function formatDate(iso: string): string {
  return fullDayFormat.format(new Date(iso))
}

export function formatMonth(iso: string): string {
  return monthFormat.format(new Date(iso))
}

export function toDateTimeLocal(iso: string): string {
  const date = new Date(iso)
  const local = date.getTime() - date.getTimezoneOffset() * 60_000
  return new Date(local).toISOString().slice(0, 16)
}

export function toDateInput(date: Date): string {
  const local = date.getTime() - date.getTimezoneOffset() * 60_000
  return new Date(local).toISOString().slice(0, 10)
}

export function formatPercent(rate: number | null): string {
  return rate === null ? 'No data' : `${Math.round(rate * 100)}%`
}
