import { useState } from 'react'
import type { FormEvent } from 'react'
import type { z } from 'zod'
import { extractErrorMessage, extractFieldErrors } from '@/lib/utils'

export function useSchemaForm<TSchema extends z.ZodType>(
  schema: TSchema,
  submit: (
    values: z.output<TSchema>,
    form: HTMLFormElement,
  ) => Promise<unknown>,
) {
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [formError, setFormError] = useState<string>()

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    setFormError(undefined)

    const parsed = schema.safeParse(Object.fromEntries(new FormData(form)))
    if (!parsed.success) {
      const next: Record<string, string> = {}
      for (const issue of parsed.error.issues) {
        next[String(issue.path[0])] ??= issue.message
      }
      setErrors(next)
      return
    }

    setErrors({})
    try {
      await submit(parsed.data, form)
    } catch (error) {
      const { non_field_errors: nonField, ...fields } =
        extractFieldErrors(error)
      setErrors(fields)
      if (nonField || Object.keys(fields).length === 0) {
        setFormError(nonField || extractErrorMessage(error))
      }
    }
  }

  return { errors, formError, handleSubmit }
}
