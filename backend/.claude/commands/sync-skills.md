---
description: Rebuild .claude/skills-index.md from installed skills
---

1. List every skill in `.claude/skills/` and read each `SKILL.md`.
2. Rewrite `.claude/skills-index.md` as a table with these columns: skill name · what it covers · when to use it in THIS project · anything to ignore (for example, Celery guidance doesn't apply because we don't use Celery).
3. In the same file, flag any skill guidance that conflicts with the Architecture section of `CLAUDE.md`, and state that those rules win.
4. Keep `CLAUDE.md` under 50 lines: change its "## Skills" section only if a skill it names was added or removed.
5. Record the sync in `.claude/brain.md`.
