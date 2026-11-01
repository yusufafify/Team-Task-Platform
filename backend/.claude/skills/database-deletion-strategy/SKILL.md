---
name: database-deletion-strategy
description: Classify each database entity into a lifecycle tier and implement the matching deletion architecture (hard delete, time-bounded soft delete, cold archive table, or immutable + PII anonymization). Use whenever designing or reviewing schemas, writing SQL migrations, configuring ORM models or relations (Prisma, TypeORM, SQLAlchemy, Hibernate, Drizzle), choosing onDelete/ON DELETE behavior, implementing DELETE endpoints or "remove"/"archive" features, handling account deletion or GDPR/CCPA erasure, adding a deleted_at/is_deleted column, or fixing broken UNIQUE constraints, dangling foreign keys or bloated indexes caused by soft deletes — even if the user only says "add a delete endpoint" or "should this be soft delete?".
---

# Database Deletion Strategy

Deletion is a per-table decision, not a schema-wide convention. A blanket `deleted_at` on every table breaks unique constraints, silences foreign-key rules, bloats hot indexes and leaks "deleted" rows into any query that forgets the filter. Classify each table into one of four tiers, then implement that tier's pattern.

## Step 0: Is it actually a deletion?

Before picking a tier, check whether the user means *delete* or a *business state*:

- **Archive / close / deactivate / finish** (a group that ended, a course that's over, a suspended account) is a status the product reads and shows. Model it as a domain column (`archived_at`, `status`), keep the row live, keep it in queries where the product wants it. This is not soft delete and needs no purge job.
- **Delete** means "this should stop existing" (created by mistake, user asked to remove it). Continue to Step 1.

If the product hasn't said whether deletion should be undoable, or for how long, ask. The grace window and retention period are product rules, not something to invent in code.

## Step 1: Classify every table

| Tier | Typical tables | Pattern |
|---|---|---|
| 1. Hard delete | Sessions, refresh tokens, OTP/reset links, caches, job/webhook queues, join tables (`user_roles`, `post_tags`, enrollments) | `DELETE`, with `ON DELETE CASCADE` from the parent |
| 2. Time-bounded soft delete | Things the product exposes in an Undo / Trash / grace-period UI: documents, projects, folders, accounts in a deactivation window | `deleted_at TIMESTAMPTZ NULL` + purge job |
| 3. Hard delete + cold archive | Audit-critical config, B2B resources, admin records that must be recoverable or explainable but aren't shown to users | Snapshot into `deleted_records`, then `DELETE`, in one transaction |
| 4. Immutable + anonymize | Invoices, payments, ledger entries, orders, clinical logs, compliance audit trails | `ON DELETE RESTRICT`; reverse with compensating entries; anonymize PII on erasure |

**Tier 1 — why hard delete:** the history of an ephemeral or join row has no business value, and keeping it bloats the hottest indexes. If you need to know *when* a role was revoked or a student left a group, write an append-only audit/event row and still hard-delete the join row.

**Tier 2 — implementation:**
- Use a timestamp, not a boolean: you need *when* to drive the purge.
- Ship the purge job with the column: a cron/worker that hard-deletes (or anonymizes) rows where `deleted_at < now() - interval '<window>'`. Soft delete without expiry quietly turns an operational table into unbounded cold storage.
- Apply the safeguards in Step 2 in the same migration.

**Tier 3 — implementation:** in one transaction, insert a snapshot and delete the live row:

```sql
BEGIN;
INSERT INTO deleted_records (entity_type, entity_id, data, deleted_by, deleted_at, reason)
SELECT 'subject', id, to_jsonb(s), $actor, now(), $reason FROM subjects s WHERE id = $id;
DELETE FROM subjects WHERE id = $id;
COMMIT;
```

The live table keeps small indexes, native UNIQUE and FK constraints, and no `WHERE deleted_at IS NULL` anyone can forget. Recovery means reinserting from the snapshot. Decide what happens to children first (Step 3, foreign-key test): either they cascade (and are snapshotted too), or the delete is refused while children exist.

**Tier 4 — implementation:** block both hard and soft delete with `ON DELETE RESTRICT` and service-level refusal. To cancel, insert a reversal entry. For GDPR/CCPA erasure, anonymize the referenced *person* row and keep its primary key so history stays valid: `email = '<uuid>@deleted.local'`, `name = 'REDACTED'`, `phone = NULL`, plus any other PII columns. Financial and clinical history must reconcile; deleting it breaks accounting and regulatory obligations.

Mixed cases are normal: a user account can be Tier 2 (30-day deactivation window), then on purge be anonymized rather than deleted because Tier 4 rows reference it.

## Step 2: Safeguards for every Tier 2 table

Setting `deleted_at` is an `UPDATE`, so the database no longer enforces what it used to. Restore it explicitly:

1. **Partial unique indexes instead of plain UNIQUE.** Otherwise a deleted user blocks re-registration with the same email:
   ```sql
   CREATE UNIQUE INDEX users_email_active_idx ON users (email) WHERE deleted_at IS NULL;
   ```
2. **Partial lookup indexes.** Add `WHERE deleted_at IS NULL` to high-traffic indexes so the planner skips dead rows.
3. **Cascades in the service transaction.** `ON DELETE CASCADE` and `ON DELETE RESTRICT` don't fire on an UPDATE. Propagate the soft delete to children, or check-and-refuse, inside one transaction.
4. **Filter at the database, not only the ORM.** ORM global filters (Prisma client extensions, Hibernate `@SQLRestriction`, TypeORM `@DeleteDateColumn`, SQLAlchemy events) are bypassed by raw SQL, views, aggregates, reporting and joins written by hand. For anything outside the ORM, use a view of active rows (`CREATE VIEW active_users AS SELECT … WHERE deleted_at IS NULL`) or row-level security.

## Step 3: Verify before finalizing

- **Re-registration test:** can a soft-deleted entity be recreated with the same email/slug/username/code without a constraint violation?
- **Foreign-key test:** does every child relation have an explicit policy (CASCADE, SET NULL, RESTRICT, or transactional propagation), and does it match the tier? Tier 4 children must never cascade-delete.
- **Retention test:** does every `deleted_at` column have a documented window and a purge/anonymization job that is actually scheduled?
- **Leak test:** grep raw SQL, views and analytics queries for the table; each one filters deleted rows or reads an active-rows view.
- **Test coverage:** the delete endpoint has tests for the chosen behavior (refused while children exist, cascades, snapshot written, re-create succeeds).

## ORM notes

- **Prisma:** referential actions are set per relation: `@relation(..., onDelete: Cascade | Restrict | SetNull | NoAction)`. Prisma 5+ removed `$use` middleware; a soft-delete filter would be a client extension (`$extends` with a `query` component), which raw queries (`$queryRaw`) bypass. If your Prisma version can't express a partial index in `schema.prisma`, add it by hand-editing the generated migration SQL, and check that the next `prisma migrate dev` doesn't generate a `DROP INDEX` for it.
- **TypeORM:** `@DeleteDateColumn` + `softRemove()` filters `find*` but not `query()` or the raw QueryBuilder (`withDeleted()` exists for opting back in). Define partial indexes in migrations.
- **SQLAlchemy:** use `Index(..., unique=True, postgresql_where=text("deleted_at IS NULL"))`; filters via `with_loader_criteria` don't apply to `text()` queries.
- **Hibernate:** `@SQLDelete` + `@SQLRestriction` rewrite entity operations only; native queries and JPQL bulk updates bypass them.
- **Drizzle:** `uniqueIndex(...).on(t.email).where(sql\`deleted_at IS NULL\`)`; there's no global filter, so every query adds the condition (another reason to prefer a view).

## Gotchas

- **`UNIQUE (email, deleted_at)` doesn't work:** NULLs are distinct in standard SQL, so two *active* rows with the same email both pass. PostgreSQL 15+ `NULLS NOT DISTINCT` fixes the active case but rejects two deletions of the same email at the same timestamp. Use the partial unique index.
- **Cold archives and backups still hold PII:** moving a user's row into `deleted_records` doesn't satisfy GDPR erasure. Scrub or hash PII in the snapshot, or purge it within the statutory window, and document how backups age out.
- **Boolean `is_deleted`:** you can't purge by age and you lose the audit timestamp. Use `deleted_at`.
- **"Soft delete everything, just in case":** this is the failure mode this skill exists to prevent. If you can't name the Undo UI or the recovery process, it isn't Tier 2.

## Output

When you apply this skill, state the tier for each affected table with a one-line reason, then the migration, model/relation changes, service logic and tests. Example:

> `refresh_tokens`: Tier 1, ephemeral, cascades from `users`.
> `subjects`: Tier 3, admin config created by mistake; delete is refused while groups exist, otherwise snapshotted and hard-deleted.
> `payments`: Tier 4, restrict; erasure anonymizes the payer.
