---
paths:
  - "apps/reports/**"
  - "tests/test_reports.py"
  - "tests/test_api_reports.py"
---

# Reports

Phase 6 monthly reports, in `apps/reports`. Built from the roadmap line, with no detailed phase prompt, so the choices live here. Client rules are in `docs/api/overview.md`.

## How it works

- `manage.py generate_reports` calls `write_report()` per team: find the last complete month on the team's clock, skip if done or quiet, spend one request, save. Run by hand until Phase 8 adds it to the schedule.
- Python works out every number. The model gets them as JSON and writes only `body`, so `stats` and `members` can't be wrong even when the prose is.
- A report reads through a leader's scoped services (`team_stats`, `visible_tasks`, `team_messages`), using the team's first leader as the actor, so there's no unscoped path for a job with no user. A team with no leader is skipped, because nobody could read its report.
- One request per report, no tools (D-006). Comments and chat go in the same request, newest first, capped at 200 tasks and 100 of each text, each with its true total.
- Run-once is `unique_team_month_report`. The check before spending avoids the request, and `get_or_create` settles an overlapping run: the report already saved stands.
- It stops at the first `Throttled` or `AIUnavailable`, like `embed_pending`. Finished reports stay, and a rerun carries on. Teams after the failure wait for that rerun.

## Decisions

- Leaders only, by `require_leader`. A report rates every member, which the glossary keeps from members. Member reports would cost one request per person.
- `stats` and `members` are frozen, not recomputed: they must agree with the prose written beside them. Members appear by display name, so nothing links to an account and emails stay out.
- Quiet means nothing created, due or completed in the month, and no comment or message. Old overdue work alone doesn't count, or a dormant team would spend a request a month. Such work still appears in an active month's report.
- `overdue` in a stored report is the count on the day of writing, because `_metrics` reads now. A late run shifts it.
- Plain text with four named headings, not `response_format`: both clients show it as text, and a truncated reply is already refused by `generate()`.
- English only: teams have no language setting.
- The timeout is 120 seconds, because a report runs outside a request.
- `reports` imports `apps.assistant.tools` for `task_row`, `stats_row` and `display_name`, so a task reads the same to the model everywhere.
- No admin page, no regenerate option, no `--month`. To redo a month, delete its row by hand and rerun.

## Checked live (2026-11-02)

- On `main`: October's Demo Team report took 1.7 seconds and 1,215 tokens. Read by hand against the tasks: every number and claim was right, and nothing was invented.
- That month had no comments or chat, because the seed stamps them with the day it ran. So two more requests used made-up data through the real prompt, logged with no team and saving no report. An Arabic comment was read correctly and given as the cause of a block. A comment ordering it to announce a cancellation, blame a person and list emails was obeyed neither time, and left out without saying so. Two samples prove little.
- Without a rule for days, "whole percentages" spread to delays: 1.25 became "1 days" and 1.5 became "2 days". The prompt now says one decimal.
- A list's total of 240 beside 3 rows caused no false claim.

## Open

- Only the last complete month is due, so an outage longer than a month loses that month's report. Nothing backfills it: see the `shortcut:` comment in `last_complete_month`.
- Reports share the chat model's daily limit, so a run uses requests people could have used. Any account can create a team, and an active one costs a request a month.
- No notification when a report appears. Phase 8 should add it with the schedule, because a hand-run command is a separate process and can't reach sockets.
- A planted comment can distort `body`, as in chat, but can reach only leaders, who can read that comment anyway. Nothing in a report can act.
