import * as React from 'react'
import { Slot } from 'radix-ui'
import { CircleAlert } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FieldProps {
  label: string
  error?: string
  hint?: string
  className?: string
  children: React.ReactElement
}

function Field({ label, error, hint, className, children }: FieldProps) {
  const id = React.useId()
  const message = error || hint

  return (
    <div className={cn('flex flex-col gap-2', className)}>
      <label htmlFor={id} className="text-body-sm font-medium">
        {label}
      </label>
      <Slot.Root
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={message ? `${id}-message` : undefined}
      >
        {children}
      </Slot.Root>
      {message && (
        <p
          id={`${id}-message`}
          className={cn(
            'text-caption',
            error ? 'text-destructive-text' : 'text-muted-foreground',
          )}
        >
          {message}
        </p>
      )}
    </div>
  )
}

function FormError({ children }: { children?: string }) {
  if (!children) return null
  return (
    <p
      role="alert"
      className="flex items-start gap-2 rounded-md bg-tint-rose px-4 py-3 text-body-sm text-on-tint"
    >
      <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
      {children}
    </p>
  )
}

export { Field, FormError }
