import { useState } from 'react'
import type { ReactElement } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { FormError } from '@/components/ui/field'
import { extractErrorMessage } from '@/lib/utils'

interface ConfirmDialogProps {
  trigger: ReactElement
  title: string
  message: string
  confirmLabel: string
  onConfirm: () => Promise<unknown>
}

export function ConfirmDialog({
  trigger,
  title,
  message,
  confirmLabel,
  onConfirm,
}: ConfirmDialogProps) {
  const [open, setOpen] = useState(false)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string>()

  async function confirm() {
    setPending(true)
    setError(undefined)
    try {
      await onConfirm()
      setOpen(false)
    } catch (failure) {
      setError(extractErrorMessage(failure))
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription>{message}</DialogDescription>
        <FormError>{error}</FormError>
        <div className="flex flex-wrap justify-end gap-3">
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button variant="destructive" disabled={pending} onClick={confirm}>
            {confirmLabel}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
