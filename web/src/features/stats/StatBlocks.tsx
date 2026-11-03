import { formatPercent } from '@/lib/format'
import type { Stats } from './types'

function formatDelay(days: number | null) {
  if (days === null) return 'No data'
  const rounded = Math.round(days * 10) / 10
  return `${rounded} ${rounded === 1 ? 'day' : 'days'}`
}

interface StatTilesProps {
  stats: Stats
}

export function StatTiles({ stats }: StatTilesProps) {
  const tiles = [
    { label: 'Due', value: stats.due },
    { label: 'Completed', value: stats.completed },
    { label: 'On time', value: stats.on_time },
    { label: 'Delayed', value: stats.delayed },
    { label: 'Overdue now', value: stats.overdue },
    { label: 'Completion rate', value: formatPercent(stats.completion_rate) },
    { label: 'On-time rate', value: formatPercent(stats.on_time_rate) },
    { label: 'Average delay', value: formatDelay(stats.average_delay_days) },
  ]

  return (
    <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-lg border bg-border md:grid-cols-4">
      {tiles.map(({ label, value }) => (
        <div key={label} className="flex flex-col gap-1 bg-card p-5">
          <dt className="text-caption text-muted-foreground">{label}</dt>
          <dd className="text-heading-4 tabular-nums">{value}</dd>
        </div>
      ))}
    </dl>
  )
}

interface MemberStatsTableProps {
  rows: ReadonlyArray<{ key: string | number; name: string; stats: Stats }>
}

export function MemberStatsTable({ rows }: MemberStatsTableProps) {
  return (
    <div
      role="region"
      aria-label="Numbers per member"
      tabIndex={0}
      className="overflow-x-auto rounded-lg border"
    >
      <table className="w-full min-w-[640px] text-left text-body-sm">
        <thead className="border-b text-caption text-muted-foreground">
          <tr>
            <th scope="col" className="px-4 py-2 font-medium">
              Member
            </th>
            <th scope="col" className="px-4 py-2 text-right font-medium">
              Due
            </th>
            <th scope="col" className="px-4 py-2 text-right font-medium">
              Completed
            </th>
            <th scope="col" className="px-4 py-2 text-right font-medium">
              Overdue now
            </th>
            <th scope="col" className="px-4 py-2 text-right font-medium">
              Completion
            </th>
            <th scope="col" className="px-4 py-2 text-right font-medium">
              On time
            </th>
            <th scope="col" className="px-4 py-2 text-right font-medium">
              Average delay
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border-soft">
          {rows.map(({ key, name, stats }) => (
            <tr key={key} className="tabular-nums">
              <th scope="row" className="px-4 py-3 font-medium">
                {name}
              </th>
              <td className="px-4 py-3 text-right">{stats.due}</td>
              <td className="px-4 py-3 text-right">{stats.completed}</td>
              <td className="px-4 py-3 text-right">{stats.overdue}</td>
              <td className="px-4 py-3 text-right">
                {formatPercent(stats.completion_rate)}
              </td>
              <td className="px-4 py-3 text-right">
                {formatPercent(stats.on_time_rate)}
              </td>
              <td className="px-4 py-3 text-right">
                {formatDelay(stats.average_delay_days)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
