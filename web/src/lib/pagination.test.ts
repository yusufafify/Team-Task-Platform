/// <reference types="node" />
import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  applyLatestPage,
  mergeIntoFirstPage,
  nextCursor,
} from './pagination.ts'
import type { InfiniteData } from '@tanstack/react-query'
import type { CursorPage } from '@/types/api'

// Run with: node --experimental-strip-types --test src/lib/pagination.test.ts
interface Item {
  id: number
}
const item = (id: number): Item => ({ id })
const page = (
  ids: Array<number>,
  next: string | null = null,
): CursorPage<Item> => ({ next, previous: null, results: ids.map(item) })
const data = (...pages: Array<CursorPage<Item>>) => ({
  pages,
  pageParams: pages.map(() => null),
})
const ids = (value: InfiniteData<CursorPage<Item>>) =>
  value.pages.map((p) => p.results.map(({ id }) => id))

test('a repeated socket event changes nothing', () => {
  const before = data(page([3, 2, 1]))
  assert.equal(mergeIntoFirstPage(before, [item(2)]), before)
})

test('a new item lands first, whatever order it arrived in', () => {
  const merged = mergeIntoFirstPage(data(page([3, 2])), [item(5), item(4)])
  assert.deepEqual(ids(merged), [[5, 4, 3, 2]])
})

test('an id on an older page is not added twice', () => {
  const merged = mergeIntoFirstPage(data(page([5]), page([4])), [item(4)])
  assert.deepEqual(ids(merged), [[5], [4]])
})

test('a latest page that overlaps merges into what is loaded', () => {
  const merged = applyLatestPage(
    data(page([3, 2], 'more'), page([1])),
    page([4, 3], 'more'),
  )
  assert.deepEqual(ids(merged), [[4, 3, 2], [1]])
})

test('a latest page that does not overlap replaces the gap', () => {
  const merged = applyLatestPage(data(page([2, 1])), page([9, 8], 'more'))
  assert.deepEqual(ids(merged), [[9, 8]])
})

test('nextCursor keeps only the cursor from next', () => {
  const next = 'http://api.example.org/teams/1/messages/?cursor=cD00ODY%3D'
  assert.equal(nextCursor(page([], next)), 'cD00ODY=')
  assert.equal(nextCursor(page([])), null)
})
