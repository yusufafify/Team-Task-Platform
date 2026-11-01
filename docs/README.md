# Docs Hub

The backend, web and mobile agents work independently and communicate only through this folder. Each agent's rules live in its own `<dir>/CLAUDE.md`, under 50 lines. There is no root `CLAUDE.md`.

## Layout

| Path | Purpose |
|------|---------|
| `status.md` | One checklist section per agent, using ✅ 🔄 ⬜. Each agent edits only its own section. |
| `api/overview.md` | Human summary of the API. Backend owns it. |
| `api/openapi.yaml` | Generated schema, created once endpoints exist. Backend owns it. |
| `api/changelog.md` | Every API change. Backend owns it. |
| `inbox/backend.md`, `inbox/web.md`, `inbox/mobile.md` | Messages addressed to that agent. |
| `decisions.md` | Project-wide decision log. |
| `glossary.md` | Shared domain terms and metric definitions. |

## Sending a message

Append an entry to the target agent's inbox, never to your own. IDs use your prefix: BE-xxx, WEB-xxx or MOB-xxx. Number them in sequence.

```markdown
### [BE-001] <short title>
- From: backend | To: web, mobile | Date: YYYY-MM-DD
- Type: notice | request | breaking-change | question
- Details: <what, which endpoints, example payload if useful>
- Status: open | accepted | done | rejected
- Resolution: <filled by receiver>
```

A message for two agents is appended to both inboxes with the same ID.

## Receiving a message

Update Status with a reason and fill in Resolution. Change nothing else in the entry. Record the last ID you processed in your handover.

## API changes

Any change to an endpoint, payload, auth behavior or error format requires all three:

1. An entry in `api/changelog.md`.
2. A regenerated `api/openapi.yaml`.
3. Notices in the web and mobile inboxes.

Changelog entry format:

```markdown
## YYYY-MM-DD — <endpoint(s)>
- Change: added | changed | removed | deprecated
- Breaking: yes/no
- Notes: <one or two lines>
```
