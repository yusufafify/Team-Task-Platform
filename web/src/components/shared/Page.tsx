import type { ReactNode } from 'react'

interface PageProps {
  title: string
  action?: ReactNode
  children: ReactNode
}

export function Page({ title, action, children }: PageProps) {
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-8 sm:px-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-heading-3">{title}</h1>
        {action}
      </div>
      {children}
    </div>
  )
}
