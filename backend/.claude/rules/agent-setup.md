---
paths:
  - ".claude/**"
  - "CLAUDE.md"
---

# Agent Setup

Permissions, skills, graphify and how the agent's own files work.

## Files and rules

- `.claude/`: memory, roadmap, commands, skills, permission rules.
- `.claude/skills-index.md`: skills table and conflict lists, read on demand.
- Keep `CLAUDE.md` under 50 lines, because agents don't read past that. There is no root `CLAUDE.md`, by the user's decision (D-011). `.claude/rules/` files without `paths` frontmatter load every session, and `@` imports load with `CLAUDE.md`, so bulky reference text belongs in an on-demand file like `skills-index.md`.
- `graphify-out/`: gitignored knowledge graph of `/backend`. `.graphifyignore` keeps `.claude/` and `skills-lock.json` out, because 270 of the 296 detected files were installed skills.
- The update command in `CLAUDE.md` sets `GRAPHIFY_OUT` because `graphify update <path>` treats `<path>` as source and writes to `<path>/graphify-out` (tested 2026-11-02 on 0.9.54). Pointing it at `graphify-out` builds a junk graph inside that folder and leaves the real one stale. `update .` from a subfolder leaves a stray `graphify-out` there.
- `graphify update` rebuilds from code without the LLM, so it drops concept nodes extracted from docs. The first run went from 105 to 634 nodes and lost 43 concepts. The old graph is in `graphify-out/curated-2026-11-01/`, because each run overwrites that day's dated backup folder (seen 2026-11-02). Only the full `/graphify` pipeline brings the concepts back, so expect the next `update` to drop them again.

## Permissions

- In `.claude/settings.json`, `/path` anchors at the working directory (`backend/`), and `../web/**` silently matches nothing (tested). The `/web` and `/mobile` rules use `//**/Nesma-Airlines/...`, so renaming the repo folder disables them.
- Deny beats allow. A `!` carve-out works only on bare or `./` deny rules listed before it in the same file (tested), so the `.env.*` rules are bare and cover `backend/` only. In `/web` and `/mobile`, only an exact `.env` is denied.
- Read and Edit deny rules were tested on built-in file tools only. They don't stop a Python script that opens files itself, including one started through `uv run`.
- Grep on `.env` returned "No matches found" with no denial (seen 2026-11-02), so an empty result there says nothing about the file.

## Skills

- Skills last synced 2026-11-01 by /sync-skills: 35 usable.
- Skills are real folders in `.claude/skills/`; the user doesn't want an `.agents/` folder. The skills installer appears to recreate `.agents/` and link into it, so copy skills in by hand.
- `gemini-api-dev` was copied from `google-gemini/gemini-skills` at commit `39d81f4`. `resend` and `email-best-practices` were copied from `resend/resend-skills` at commit `b2ae7b1`.
