import { ShieldCheck } from 'lucide-react'
import { EmptyState } from '@/components/shared/States'

interface LeadersOnlyProps {
  title: string
}

export function LeadersOnly({ title }: LeadersOnlyProps) {
  return (
    <EmptyState
      icon={ShieldCheck}
      title={title}
      message="Only this team's leaders can open this page. Ask a leader if you need something from it."
    />
  )
}
