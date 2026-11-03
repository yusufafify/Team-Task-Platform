import { useState } from 'react';
import type { z } from 'zod';

import { errorMessage, fieldErrors } from '@/lib/http';

// Validates with the schema, then maps the API's 400 field errors back onto the same fields.
export function useSchemaForm<S extends z.ZodObject>(
  schema: S,
  initial: z.input<S>,
  submit: (values: z.output<S>) => Promise<unknown>,
) {
  const [values, setValues] = useState(initial);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string>();
  const [submitting, setSubmitting] = useState(false);

  function set<K extends keyof z.input<S>>(key: K, value: z.input<S>[K]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit() {
    if (submitting) return;
    setFormError(undefined);
    const parsed = schema.safeParse(values);
    if (!parsed.success) {
      const next: Record<string, string> = {};
      for (const issue of parsed.error.issues) next[String(issue.path[0])] ??= issue.message;
      setErrors(next);
      return;
    }

    setErrors({});
    setSubmitting(true);
    try {
      await submit(parsed.data);
    } catch (error) {
      const { non_field_errors: nonField, ...fields } = fieldErrors(error);
      setErrors(fields);
      if (nonField || Object.keys(fields).length === 0) setFormError(nonField || errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  }

  return { values, set, errors, formError, submitting, handleSubmit };
}
