import * as React from 'react'
import { cva } from 'class-variance-authority'
import type { VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

// Status badges are pills; tags are soft 6px chips on a tint. The pink and orange fills use the deep
// brand shades because white text fails contrast on the bright ones.
const badgeVariants = cva(
  'inline-flex w-fit items-center whitespace-nowrap text-caption-bold',
  {
    variants: {
      variant: {
        purple: 'rounded-full bg-primary px-2.5 py-1 text-primary-foreground',
        pink: 'rounded-full bg-brand-pink-deep px-2.5 py-1 text-on-dark',
        orange: 'rounded-full bg-brand-orange-deep px-2.5 py-1 text-on-dark',
        'tag-purple': 'rounded-sm bg-tint-lavender px-2 py-0.5 text-tag-purple',
        'tag-orange': 'rounded-sm bg-tint-peach px-2 py-0.5 text-tag-orange',
        'tag-green': 'rounded-sm bg-tint-mint px-2 py-0.5 text-tag-green',
        'tag-gray': 'rounded-sm bg-tint-gray px-2 py-0.5 text-on-tint',
      },
    },
    defaultVariants: {
      variant: 'purple',
    },
  },
)

function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<'span'> & VariantProps<typeof badgeVariants>) {
  return (
    <span
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge }
