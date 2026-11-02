import * as React from 'react'
import { cva } from 'class-variance-authority'
import type { VariantProps } from 'class-variance-authority'
import { Slot } from 'radix-ui'
import { cn } from '@/lib/utils'

// Rectangular 8px buttons, never pills. default is the one dominant action per view.
const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2 rounded-md text-button whitespace-nowrap transition-colors duration-150 disabled:pointer-events-none [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default:
          'bg-primary text-primary-foreground hover-device:hover:bg-primary/90 active:bg-primary-pressed disabled:bg-border disabled:text-muted-foreground',
        dark: 'bg-inverse text-inverse-foreground hover-device:hover:bg-inverse/85 active:bg-inverse/75 disabled:bg-border disabled:text-muted-foreground',
        outline:
          'border border-border-strong text-foreground hover-device:hover:bg-secondary active:bg-tint-gray disabled:opacity-50',
        outlineOnDark:
          'border border-on-dark-muted text-on-dark hover-device:hover:bg-on-dark/10 active:bg-on-dark/15',
        ghost:
          'rounded-sm text-foreground hover-device:hover:bg-secondary active:bg-tint-gray disabled:opacity-50',
        link: 'text-body-sm font-medium text-link underline-offset-4 hover-device:hover:underline active:text-link-pressed disabled:opacity-50',
        destructive:
          'bg-destructive text-destructive-foreground hover-device:hover:bg-destructive/90 disabled:bg-border disabled:text-muted-foreground',
      },
      // 44px on touch, the spec's 40px on desktop. sm is for dense toolbars and tables only.
      size: {
        default: 'h-11 px-[18px] lg:h-10',
        sm: 'h-9 px-3',
        icon: 'size-11 lg:size-10',
      },
    },
    compoundVariants: [{ variant: 'link', className: 'h-auto px-0 lg:h-auto' }],
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

function Button({
  className,
  variant = 'default',
  size = 'default',
  asChild = false,
  ...props
}: React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot.Root : 'button'

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
