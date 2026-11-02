import * as React from 'react'
import { cn } from '@/lib/utils'

function Input({ className, type, ...props }: React.ComponentProps<'input'>) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        'h-11 w-full min-w-0 rounded-md border border-input bg-card px-4 text-body-md text-foreground outline-none transition-colors duration-150 placeholder:text-steel disabled:pointer-events-none disabled:bg-muted disabled:text-muted-foreground',
        // A 2px border when focused; the inset shadow adds the second pixel without shifting the layout.
        'focus-visible:border-ring focus-visible:shadow-[inset_0_0_0_1px_var(--ring)]',
        'aria-invalid:border-destructive-text',
        className,
      )}
      {...props}
    />
  )
}

export { Input }
