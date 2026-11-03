import type { InfiniteData } from '@tanstack/react-query'
import type { CursorPage } from '@/types/api'

type CursorData<T> = InfiniteData<CursorPage<T>>

// Takes only the cursor from `next`, because its host can be the API's own domain, where cookies don't go.
export function nextCursor(page: CursorPage<unknown>): string | null {
  return page.next
    ? new URL(page.next, 'http://localhost').searchParams.get('cursor')
    : null
}

function knownIds<T extends { id: number }>(data: CursorData<T>) {
  return new Set(data.pages.flatMap((page) => page.results.map(({ id }) => id)))
}

// Threads are newest first, and the same item can arrive by socket and by REST.
export function mergeIntoFirstPage<T extends { id: number }>(
  data: CursorData<T>,
  incoming: ReadonlyArray<T>,
): CursorData<T> {
  const known = knownIds(data)
  const fresh = incoming.filter(({ id }) => !known.has(id))
  if (fresh.length === 0) return data

  const [first, ...rest] = data.pages
  const results = [...fresh, ...first.results].sort((a, b) => b.id - a.id)
  return { ...data, pages: [{ ...first, results }, ...rest] }
}

export function applyLatestPage<T extends { id: number }>(
  data: CursorData<T>,
  latest: CursorPage<T>,
): CursorData<T> {
  const known = knownIds(data)
  const joinsUp = !latest.next || latest.results.some(({ id }) => known.has(id))
  // More than a page arrived while offline, so older pages no longer join this one.
  return joinsUp
    ? mergeIntoFirstPage(data, latest.results)
    : { pages: [latest], pageParams: [null] }
}
