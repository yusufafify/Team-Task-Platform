import { useState } from 'react'
import { ErrorState } from '@/components/shared/States'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { Button } from '@/components/ui/button'
import { Field, FormError } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useMe } from '@/features/auth/query'
import { useSchemaForm } from '@/hooks/useSchemaForm'
import { displayName } from '@/lib/format'
import { extractErrorMessage } from '@/lib/utils'
import {
  useAddMember,
  useChangeMemberRole,
  useMembers,
  useRemoveMember,
  useTeam,
} from './query'
import { addMemberSchema, teamRoleSchema } from './schema'
import type { Member } from './types'

interface AddMemberFormProps {
  teamId: number
}

function AddMemberForm({ teamId }: AddMemberFormProps) {
  const add = useAddMember(teamId)
  const { errors, formError, handleSubmit } = useSchemaForm(
    addMemberSchema,
    async (values, form) => {
      await add.mutateAsync(values)
      form.reset()
    },
  )

  return (
    <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
      <h2 className="text-heading-5">Add a member</h2>
      <FormError>{formError}</FormError>
      <div className="grid items-start gap-4 sm:grid-cols-[minmax(0,1fr)_140px_auto]">
        <Field
          label="Email"
          error={errors.email}
          hint="They need an account already."
        >
          <Input name="email" type="email" autoComplete="off" required />
        </Field>
        <Field label="Role" error={errors.role}>
          <Select name="role" defaultValue="member">
            <option value="member">Member</option>
            <option value="leader">Leader</option>
          </Select>
        </Field>
        <Button type="submit" disabled={add.isPending} className="sm:mt-7">
          Add member
        </Button>
      </div>
    </form>
  )
}

interface MemberRowProps {
  teamId: number
  member: Member
  isSelf: boolean
  canManage: boolean
}

function MemberRow({ teamId, member, isSelf, canManage }: MemberRowProps) {
  const changeRole = useChangeMemberRole(teamId)
  const remove = useRemoveMember(teamId)
  const name = displayName(member.user)
  const [error, setError] = useState<string>()

  return (
    <li className="flex flex-col gap-2 px-5 py-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="min-w-0 flex-1 basis-full sm:basis-0">
          <p className="text-body-md font-medium">
            {name}
            {isSelf && ' (you)'}
          </p>
          <p className="text-body-sm text-muted-foreground">
            {member.user.email}
          </p>
        </div>
        {canManage ? (
          <>
            <Select
              aria-label={`Role for ${name}`}
              className="h-11 w-32 lg:h-9"
              value={member.role}
              disabled={changeRole.isPending}
              onChange={(event) => {
                setError(undefined)
                changeRole.mutate(
                  {
                    userId: member.user.id,
                    role: teamRoleSchema.parse(event.target.value),
                  },
                  {
                    onError: (failure) =>
                      setError(extractErrorMessage(failure)),
                  },
                )
              }}
            >
              <option value="member">Member</option>
              <option value="leader">Leader</option>
            </Select>
            <ConfirmDialog
              trigger={
                <Button variant="outline" size="sm">
                  Remove
                </Button>
              }
              title={`Remove ${name}?`}
              message="Their unfinished tasks become unassigned. Finished tasks keep their name."
              confirmLabel="Remove member"
              onConfirm={() => remove.mutateAsync(member.user.id)}
            />
          </>
        ) : (
          <span className="text-body-sm text-muted-foreground">
            {member.role === 'leader' ? 'Leader' : 'Member'}
          </span>
        )}
      </div>
      <FormError>{error}</FormError>
    </li>
  )
}

interface MembersPageProps {
  teamId: number
}

export function MembersPage({ teamId }: MembersPageProps) {
  const team = useTeam(teamId)
  const me = useMe()
  const { data: members, error, refetch } = useMembers(teamId)
  const canManage = team.role === 'leader'

  if (error) {
    return <ErrorState error={error} onRetry={() => void refetch()} />
  }

  return (
    <>
      {canManage && <AddMemberForm teamId={teamId} />}
      {!members ? (
        <div aria-busy="true" className="flex flex-col gap-3">
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
        </div>
      ) : (
        <ul className="divide-y rounded-lg border">
          {members.map((member) => (
            <MemberRow
              key={member.user.id}
              teamId={teamId}
              member={member}
              isSelf={member.user.id === me.id}
              canManage={canManage}
            />
          ))}
        </ul>
      )}
    </>
  )
}
