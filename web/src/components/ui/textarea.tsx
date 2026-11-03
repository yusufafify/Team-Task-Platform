import * as React from 'react'
import { cn } from '@/lib/utils'

function Textarea({ className, ...props }: React.ComponentProps<'textarea'>) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        'min-h-24 w-full min-w-0 rounded-md border border-input bg-card px-4 py-3 text-body-md text-foreground outline-none transition-colors duration-150 placeholder:text-steel disabled:pointer-events-none disabled:bg-muted disabled:text-muted-foreground',
        'focus-visible:border-ring focus-visible:shadow-[inset_0_0_0_1px_var(--ring)]',
        'aria-invalid:border-destructive-text',
        className,
      )}
      {...props}
    />
  )
}

export { Textarea }
