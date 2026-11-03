import type { InfiniteData } from '@tanstack/react-query';

import type { CursorPage, Paginated } from '@/lib/types';

type CursorData<T> = InfiniteData<CursorPage<T>>;

// Takes only the cursor from `next`, so the facade keeps choosing the host and the token.
export function nextCursor(page: CursorPage<unknown>): string | null {
  const match = page.next?.match(/[?&]cursor=([^&]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export function nextPage(last: Paginated<unknown>, _all: unknown, page: number) {
  return last.next ? page + 1 : undefined;
}

function knownIds<T extends { id: number }>(data: CursorData<T>) {
  return new Set(data.pages.flatMap((page) => page.results.map(({ id }) => id)));
}

// Threads are newest first, and the same item can arrive by socket and by REST.
export function mergeIntoFirstPage<T extends { id: number }>(
  data: CursorData<T>,
  incoming: readonly T[],
): CursorData<T> {
  const known = knownIds(data);
  const fresh = incoming.filter(({ id }) => !known.has(id));
  if (fresh.length === 0) return data;

  const [first, ...rest] = data.pages;
  const results = [...fresh, ...first.results].sort((a, b) => b.id - a.id);
  return { ...data, pages: [{ ...first, results }, ...rest] };
}

export function applyLatestPage<T extends { id: number }>(
  data: CursorData<T>,
  latest: CursorPage<T>,
): CursorData<T> {
  const known = knownIds(data);
  const joinsUp = !latest.next || latest.results.some(({ id }) => known.has(id));
  // More than a page arrived while away, so older pages no longer join this one.
  return joinsUp ? mergeIntoFirstPage(data, latest.results) : { pages: [latest], pageParams: [null] };
}
