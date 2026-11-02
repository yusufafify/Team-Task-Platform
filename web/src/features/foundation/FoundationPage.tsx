import ThemeToggle from '@/components/ThemeToggle'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const STICKY_NOTES = [
  'top-[16%] left-[7%] size-11 -rotate-12 bg-brand-yellow',
  'top-[34%] left-[15%] size-7 rotate-6 bg-brand-pink',
  'top-[58%] left-[6%] size-9 rotate-12 bg-brand-teal',
  'top-[14%] right-[9%] size-9 rotate-12 bg-brand-orange',
  'top-[36%] right-[16%] size-11 -rotate-6 bg-brand-purple',
  'top-[60%] right-[6%] size-7 -rotate-12 bg-brand-green',
]

const BOARD = [
  {
    title: 'To do',
    tag: 'tag-purple',
    tasks: ['Review crew roster', 'Draft cabin checklist'],
  },
  {
    title: 'In progress',
    tag: 'tag-orange',
    tasks: ['Update station contacts'],
  },
  {
    title: 'Done',
    tag: 'tag-green',
    tasks: ['Send monthly report', 'Close safety audit'],
  },
] as const

const TINTS = [
  { name: 'Peach', className: 'bg-tint-peach' },
  { name: 'Rose', className: 'bg-tint-rose' },
  { name: 'Mint', className: 'bg-tint-mint' },
  { name: 'Lavender', className: 'bg-tint-lavender' },
  { name: 'Sky', className: 'bg-tint-sky' },
  { name: 'Yellow', className: 'bg-tint-yellow' },
]

export function FoundationPage() {
  return (
    <>
      <header className="sticky top-0 z-20 h-16 border-b bg-background">
        <div className="mx-auto flex h-full max-w-page items-center justify-between px-4 sm:px-8">
          <span className="text-heading-5">Nesma Airlines</span>
          <ThemeToggle />
        </div>
      </header>

      <main>
        <section className="relative flow-root bg-brand-navy px-4 pt-section-lg text-center text-on-dark sm:px-8 lg:pt-hero">
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

          <div className="relative mx-auto max-w-3xl">
            <h1 className="text-heading-2 sm:text-heading-1 md:text-display-lg xl:text-hero-display">
              Nesma Airlines
            </h1>
            <p className="mt-6 text-subtitle text-on-dark-muted">
              The web foundation: TanStack Start in SPA mode, styled with
              Notion&rsquo;s design language. Features land here next.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Button asChild>
                <a href="#components">View components</a>
              </Button>
              <Button asChild variant="outlineOnDark">
                <a href="#colors">View colours</a>
              </Button>
            </div>
          </div>

          <div className="relative mx-auto -mb-section mt-section-sm max-w-[960px] overflow-hidden rounded-lg border bg-card text-left text-card-foreground shadow-mockup">
            <div className="flex items-center justify-between gap-3 border-b px-6 py-4">
              <span className="text-heading-5">Sample board</span>
              <Badge variant="tag-purple">Preview</Badge>
            </div>
            <div className="grid gap-4 bg-surface-soft p-6 md:grid-cols-3">
              {BOARD.map((column) => (
                <div key={column.title} className="flex flex-col gap-3">
                  <Badge variant={column.tag}>{column.title}</Badge>
                  {column.tasks.map((task) => (
                    <div
                      key={task}
                      className="rounded-md border bg-card px-3 py-2 text-body-sm shadow-subtle"
                    >
                      {task}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section
          id="components"
          className="mx-auto mt-section max-w-page scroll-mt-16 px-4 py-section-lg sm:px-8"
        >
          <h2 className="text-heading-3 md:text-heading-2">Components</h2>
          <p className="mt-2 text-body-md text-muted-foreground">
            The shared controls in src/components/ui, built to the nesma-design
            skill.
          </p>
          <div className="mt-8 grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Buttons</CardTitle>
                <CardDescription>
                  One purple action per view; everything else steps back.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap items-center gap-3">
                <Button>Primary</Button>
                <Button variant="dark">Dark</Button>
                <Button variant="outline">Secondary</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="destructive">Delete</Button>
                <Button variant="link">Text link</Button>
                <Button disabled>Disabled</Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Inputs and badges</CardTitle>
                <CardDescription>
                  Status badges are pills; tags are soft chips.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <label className="flex flex-col gap-2 text-body-sm font-medium">
                  Flight number
                  <Input placeholder="e.g. NE 100" />
                </label>
                <div className="flex flex-wrap gap-2">
                  <Badge>New</Badge>
                  <Badge variant="pink">Beta</Badge>
                  <Badge variant="orange">Pending</Badge>
                  <Badge variant="tag-purple">Crew</Badge>
                  <Badge variant="tag-orange">Delayed</Badge>
                  <Badge variant="tag-green">On time</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <section
          id="colors"
          className="mx-auto max-w-page scroll-mt-16 px-4 pb-section-lg sm:px-8"
        >
          <h2 className="text-heading-3 md:text-heading-2">Colours</h2>
          <p className="mt-2 text-body-md text-muted-foreground">
            Pastel tints carry the colour; purple stays reserved for the main
            action.
          </p>
          <div className="mt-8 rounded-lg bg-tint-yellow-bold p-8 text-on-tint">
            <p className="text-heading-4">Bold yellow</p>
            <p className="mt-2 text-body-md">
              Reserved for the one high-emphasis banner in a section.
            </p>
          </div>
          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {TINTS.map((tint) => (
              <div
                key={tint.name}
                className={cn('rounded-lg p-8 text-on-tint', tint.className)}
              >
                <p className="text-heading-4">{tint.name}</p>
                <p className="mt-2 text-body-sm">{tint.className}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </>
  )
}
