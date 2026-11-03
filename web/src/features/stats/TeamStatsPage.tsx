// Not StatsPage.tsx: content blockers refuse URLs ending in /statspage.*, and dev serves files by name.
import { ErrorState } from '@/components/shared/States'
import { Button } from '@/components/ui/button'
import { Field } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { displayName, formatDate } from '@/lib/format'
import { cn } from '@/lib/utils'
import { useTeamStats } from './query'
import { MemberStatsTable, StatTiles } from './StatBlocks'
import type { StatsPeriod } from './types'

interface TeamStatsPageProps {
  teamId: number
  period: StatsPeriod
  onPeriodChange: (period: StatsPeriod) => void
}

export function TeamStatsPage({
  teamId,
  period,
  onPeriodChange,
}: TeamStatsPageProps) {
  const { data, error, refetch, isPlaceholderData } = useTeamStats(
    teamId,
    period,
  )

  return (
    <>
      <div className="flex flex-wrap items-end gap-3">
        <Field label="From">
          <Input
            type="date"
            className="w-auto text-body-sm"
            value={period.start ?? data?.start ?? ''}
            onChange={({ target }) =>
              onPeriodChange({ ...period, start: target.value || undefined })
            }
          />
        </Field>
        <Field label="To">
          <Input
            type="date"
            className="w-auto text-body-sm"
            value={period.end ?? data?.end ?? ''}
            onChange={({ target }) =>
              onPeriodChange({ ...period, end: target.value || undefined })
            }
          />
        </Field>
        {(period.start || period.end) && (
          <Button variant="outline" onClick={() => onPeriodChange({})}>
            This month
          </Button>
        )}
      </div>

      {error ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : !data ? (
        <Skeleton aria-busy="true" className="h-48" />
      ) : (
        <div
          className={cn(
            'flex flex-col gap-6 transition-opacity duration-150',
            isPlaceholderData && 'opacity-60',
          )}
        >
          <p className="text-body-sm text-muted-foreground">
            {data.scope === 'team' ? 'The whole team' : 'Your own numbers'},{' '}
            {formatDate(data.start)} to {formatDate(data.end)}, counted in{' '}
            {data.timezone}. Completion can pass 100%, because it compares tasks
            completed in this period with tasks due in it.
          </p>
          <StatTiles stats={data.stats} />
          {data.members.length > 0 && (
            <section className="flex flex-col gap-3">
              <h2 className="text-heading-5">By member</h2>
              <MemberStatsTable
                rows={data.members.map(({ user, stats }) => ({
                  key: user.id,
                  name: displayName(user),
                  stats,
                }))}
              />
            </section>
          )}
        </div>
      )}
    </>
  )
}
