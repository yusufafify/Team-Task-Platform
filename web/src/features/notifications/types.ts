export interface Notification {
  id: number
  // A plain string: new kinds can arrive, and clients must accept them.
  kind: string
  title: string
  body: string
  task: number | null
  read_at: string | null
  created_at: string
}
