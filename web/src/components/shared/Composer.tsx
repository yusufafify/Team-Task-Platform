import { useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { FormError } from '@/components/ui/field'
import { Textarea } from '@/components/ui/textarea'
import { extractErrorMessage } from '@/lib/utils'

interface ComposerProps {
  label: string
  submitLabel: string
  maxLength: number
  onSend: (text: string) => Promise<unknown>
  describeError?: (error: unknown) => string
}

// Keeps the text until the send succeeds, because a failed message isn't saved anywhere.
export function Composer({
  label,
  submitLabel,
  maxLength,
  onSend,
  describeError = extractErrorMessage,
}: ComposerProps) {
  const [text, setText] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string>()
  // A ref, because state stays stale until the next render, which lets a double submit through.
  const sending = useRef(false)

  async function send() {
    const body = text.trim()
    if (!body || sending.current) return
    sending.current = true
    setPending(true)
    setError(undefined)
    try {
      await onSend(body)
      setText('')
    } catch (failure) {
      setError(describeError(failure))
    } finally {
      sending.current = false
      setPending(false)
    }
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        void send()
      }}
      className="flex shrink-0 flex-col gap-2 border-t p-3"
    >
      <FormError>{error}</FormError>
      <div className="flex items-end gap-2">
        <Textarea
          aria-label={label}
          placeholder={label}
          rows={1}
          maxLength={maxLength}
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (
              event.key === 'Enter' &&
              !event.shiftKey &&
              !event.nativeEvent.isComposing
            ) {
              event.preventDefault()
              void send()
            }
          }}
          className="max-h-40 min-h-11 flex-1 resize-none py-2.5"
        />
        <Button type="submit" disabled={pending || !text.trim()}>
          {submitLabel}
        </Button>
      </div>
    </form>
  )
}
