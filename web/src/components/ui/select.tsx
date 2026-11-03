import * as React from 'react'
import { cn } from '@/lib/utils'

// Native on purpose: the OS picker is the best control on touch, and needs no custom keyboard handling.
function Select({ className, ...props }: React.ComponentProps<'select'>) {
  return (
    <select
      data-slot="select"
      className={cn(
        'h-11 w-full min-w-0 cursor-pointer rounded-md border border-input bg-card px-3 text-body-sm text-foreground outline-none transition-colors duration-150 disabled:pointer-events-none disabled:bg-muted disabled:text-muted-foreground',
        'focus-visible:border-ring focus-visible:shadow-[inset_0_0_0_1px_var(--ring)]',
        'aria-invalid:border-destructive-text',
        className,
      )}
      {...props}
    />
  )
}

export { Select }
