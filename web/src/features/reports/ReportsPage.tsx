import { useState } from 'react'
import { FileText } from 'lucide-react'
import { EmptyState, ErrorState } from '@/components/shared/States'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { MemberStatsTable, StatTiles } from '@/features/stats/StatBlocks'
import { LeadersOnly } from '@/features/teams/LeadersOnly'
import { useTeam } from '@/features/teams/query'
import { formatDate, formatMonth } from '@/lib/format'
import { cn } from '@/lib/utils'
import { useReports } from './query'

interface ReportsPageProps {
  teamId: number
}

export function ReportsPage({ teamId }: ReportsPageProps) {
  const team = useTeam(teamId)
  const isLeader = team.role === 'leader'
  const {
    data,
    error,
    refetch,
    hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
  } = useReports(teamId, isLeader)
  const [selectedId, setSelectedId] = useState<number>()
  const reports = data?.pages.flatMap((page) => page.results)
  const report = reports?.find(({ id }) => id === selectedId) ?? reports?.[0]

  if (!isLeader) {
    return <LeadersOnly title="Monthly reports" />
  }
  if (error) {
    return <ErrorState error={error} onRetry={() => void refetch()} />
  }
  if (!reports) {
    return <Skeleton aria-busy="true" className="h-64" />
  }
  if (!report) {
    return (
      <EmptyState
        icon={FileText}
        title="No reports yet"
        message="A report is written within a day of each month ending. A month with no activity doesn't get one."
      />
    )
  }

  return (
    <div className="grid gap-6 md:grid-cols-[180px_minmax(0,1fr)]">
      <nav aria-label="Report months" className="flex flex-col gap-1">
        {reports.map(({ id, month }) => (
          <button
            key={id}
            type="button"
            aria-current={id === report.id ? 'true' : undefined}
            onClick={() => setSelectedId(id)}
            className={cn(
              'h-11 rounded-sm px-3 text-left text-body-sm font-medium text-muted-foreground transition-colors duration-150 hover-device:hover:bg-secondary md:h-9',
              id === report.id && 'bg-secondary text-foreground',
            )}
          >
            {formatMonth(month)}
          </button>
        ))}
        {hasNextPage && (
          <Button
            variant="ghost"
            size="sm"
            disabled={isFetchingNextPage}
            onClick={() => void fetchNextPage()}
          >
            Show older reports
          </Button>
        )}
      </nav>

      <article className="flex min-w-0 flex-col gap-6">
        <div className="flex flex-col gap-1">
          <h2 className="text-heading-4">{formatMonth(report.month)}</h2>
          <p className="text-body-sm text-muted-foreground">
            Written {formatDate(report.created_at)}. These numbers were fixed
            then, so they can differ from live stats.
          </p>
        </div>
        <StatTiles stats={report.stats} />
        {/* AI text that can repeat what others wrote, so it stays plain text. */}
        <p className="text-body-md whitespace-pre-wrap">{report.body}</p>
        {report.members.length > 0 && (
          <section className="flex flex-col gap-3">
            <h3 className="text-heading-5">By member</h3>
            <MemberStatsTable
              rows={report.members.map(({ name, stats }) => ({
                key: name,
                name,
                stats,
              }))}
            />
          </section>
        )}
      </article>
    </div>
  )
}
