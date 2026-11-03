import { Link, useRouter } from '@tanstack/react-router'
import type { ErrorComponentProps } from '@tanstack/react-router'
import { AlertTriangle, Compass } from 'lucide-react'
import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { extractErrorMessage, extractRequestId } from '@/lib/utils'

interface FallbackProps {
  icon: ReactNode
  title: string
  message: string
  action: ReactNode
}

function Fallback({ icon, title, message, action }: FallbackProps) {
  return (
    <div
      role="alert"
      className="flex min-h-[60vh] w-full items-center justify-center p-4 sm:p-8"
    >
      <div className="flex max-w-md flex-col items-center gap-4 text-center">
        <div className="flex size-14 items-center justify-center rounded-lg bg-secondary text-muted-foreground">
          {icon}
        </div>
        <h1 className="text-heading-4 text-foreground">{title}</h1>
        <p className="text-body-md text-muted-foreground">{message}</p>
        {action}
      </div>
    </div>
  )
}

export function RouteError({ error }: ErrorComponentProps) {
  const router = useRouter()
  const requestId = extractRequestId(error)
  return (
    <Fallback
      icon={<AlertTriangle className="size-7" aria-hidden="true" />}
      title="This page couldn't load"
      message={
        extractErrorMessage(error) +
        (requestId ? ` Reference: ${requestId}` : '')
      }
      action={<Button onClick={() => router.invalidate()}>Try again</Button>}
    />
  )
}

export function RouteNotFound() {
  return (
    <Fallback
      icon={<Compass className="size-7" aria-hidden="true" />}
      title="Page not found"
      message="The link may be old, or the page may have moved."
      action={
        <Button asChild>
          <Link to="/">Go home</Link>
        </Button>
      }
    />
  )
}
