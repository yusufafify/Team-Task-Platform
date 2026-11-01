---
paths:
  - "apps/**/models.py"
  - "apps/**/admin.py"
  - "apps/**/services.py"
---

# Domain Model

Schema choices made in Phase 1 from the roadmap and glossary, because no detailed phase prompt existed. `docs/decisions.md` is outside this agent's edit list, so they live here.

- Login is by email. `username` is removed, and `UserManager.normalize_email` lowercases the whole address. `AbstractUser.clean()` calls it too, so forms and the manager agree, and `get_by_natural_key` makes login ignore case.
- The leader or member role sits on `TeamMembership`, so a user can hold different roles on different teams.
- A task has one optional `assignee` and a required `due_at`. A required date keeps the completion and on-time rates free of null cases, and loosening it later is an easy migration.
- `Task.completed_at` is set exactly when the status is done, enforced by a database constraint. The Phase 2 service must set it on done and clear it on reopening.
- The database can't check that an assignee or author belongs to the team. Phase 2 services must, and the admin doesn't.
- Overdue, delayed and the rates stay computed, never stored.
- `DeviceToken` needs no platform, because Expo's token already identifies the device. Changing Python-only choices, like `Notification.Kind`, creates a migration with no SQL.
- Task lists use only their foreign-key indexes for now. Add composite indexes when a Phase 2 stats query needs them.

## Deletion tiers

- `TeamMembership`, `DeviceToken`, `Notification`: hard delete, cascading from their parent.
- `Task`, `Comment`: hard delete, because no Undo screen exists. Comments and notifications cascade from the task.
- `Message`: hard delete, held by `PROTECT` on team and author.
- `User`: `PROTECT` from every task, comment and message they appear on. Set `is_active=False` instead. Account erasure, when it's needed, should anonymize the row and keep its key.
- `Team`: `PROTECT` from tasks and messages, so only an empty team can be deleted. Django's `on_delete` lives in Python, so changing it needs no schema change.
