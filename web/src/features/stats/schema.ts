import { z } from 'zod'

export const statsSearchSchema = z.object({
  start: z.iso.date().optional().catch(undefined),
  end: z.iso.date().optional().catch(undefined),
})
