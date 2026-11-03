export interface User {
  id: number
  email: string
  first_name?: string
  last_name?: string
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: Array<T>
}

export interface CursorPage<T> {
  next: string | null
  previous: string | null
  results: Array<T>
}
