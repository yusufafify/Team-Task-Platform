import { Outlet } from '@tanstack/react-router'
import { cn } from '@/lib/utils'

const STICKY_NOTES = [
  'top-[14%] left-[8%] size-11 -rotate-12 bg-brand-yellow',
  'top-[42%] left-[14%] size-7 rotate-6 bg-brand-pink',
  'top-[70%] left-[6%] size-9 rotate-12 bg-brand-teal',
  'top-[12%] right-[9%] size-9 rotate-12 bg-brand-orange',
  'top-[46%] right-[15%] size-11 -rotate-6 bg-brand-purple',
  'top-[74%] right-[7%] size-7 -rotate-12 bg-brand-green',
]

export function AuthLayout() {
  return (
    <div className="relative flex min-h-dvh flex-col items-center justify-center gap-8 bg-brand-navy px-4 py-section-sm text-center text-on-dark">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 hidden overflow-hidden md:block"
      >
        <svg
          viewBox="0 0 1200 600"
          preserveAspectRatio="none"
          fill="none"
          stroke="currentColor"
          className="size-full text-brand-navy-mid"
        >
          <path d="M0 120 C 240 40, 320 300, 560 180 S 980 60, 1200 220" />
          <path d="M0 260 C 200 200, 360 420, 600 300 S 1000 200, 1200 360" />
          <path d="M0 420 C 260 340, 380 540, 640 440 S 1020 360, 1200 500" />
        </svg>
        {STICKY_NOTES.map((note) => (
          <span key={note} className={cn('absolute rounded-sm', note)} />
        ))}
      </div>

      <div className="relative flex max-w-xl flex-col gap-3">
        <p className="text-heading-5">Nesma Airlines</p>
        <p className="text-heading-3 sm:text-heading-2">
          Your team&rsquo;s work, in order of what&rsquo;s due next.
        </p>
      </div>

      <main className="relative w-full max-w-md rounded-lg border bg-card p-6 text-left text-card-foreground shadow-mockup sm:p-8">
        <Outlet />
      </main>
    </div>
  )
}
