# Backend Brain

Index only: this is the one map of backend memory. Regions in `.claude/rules/` load by themselves when you touch a matching file. Plain shell commands don't trigger them, so before shell-only work, load the matching region yourself.

| Region | Holds | Loads by itself on | Load by hand when |
|---|---|---|---|
| `.claude/handover.md` | Current state, next steps, blockers | Never | Every session start |
| `.claude/roadmap.md` | The phases and what each delivers | Never | Planning or starting a phase |
| `.claude/rules/architecture.md` | What's built, file map, environment variables | `config/`, `apps/`, `manage.py`, `.env.example` | Explaining how the project is built |
| `.claude/rules/api.md` | API patterns, error format, Phase 2 decisions | Views, serializers, urls, throttles | Designing an endpoint or changing auth |
| `.claude/rules/api-limits.md` | Login limits, accepted risks, what isn't built | Views, urls, throttles | Changing auth, or planning Phase 8 hosting |
| `.claude/rules/domain-model.md` | Schema choices and deletion tiers | Models, admin, services | Designing a model or a delete path |
| `.claude/rules/scheduling.md` | How scheduled jobs run, and host and Neon limits | Management commands, `tasks.py` | Planning Phase 8, or choosing a host |
| `.claude/rules/database.md` | Neon branches, connections, migrations | Models, migrations, settings, `manage.py`, `.env.example` | Running `migrate` or any database command |
| `.claude/rules/testing.md` | pytest setup, test database rules | `tests/`, `test.py`, `pyproject.toml` | Running pytest, or debugging a failure |
| `.claude/rules/ai.md` | LLM gateway, limits, call log, SDK traps, data-use terms | `apps/ai/`, `tests/test_ai.py` | Planning Phases 4 to 6, or any Gemini work |
| `.claude/rules/assistant.md` | Chatbot flow, snapshot, tools, answer cache, seed command | `apps/assistant/`, `apps/teams/management/`, assistant and seed tests | Changing the chatbot, or planning Phase 5 |
| `.claude/rules/tooling.md` | Commands, uv, ruff, Windows quirks | `pyproject.toml`, `uv.lock`, `.python-version` | Installing, running commands, tool errors |
| `.claude/rules/agent-setup.md` | Permissions, skills, graphify, `CLAUDE.md` limits | `.claude/`, `CLAUDE.md` | Permission or skill problems |
| `.claude/skills-index.md` | Every skill, what to ignore, conflicts | Never | Before relying on a skill |
| `../docs/decisions.md` | Full decision log, the D-xxx IDs | Never | A change or skill may conflict with a decision |

## Rules

- Save durable facts only, each in the region it belongs to.
- New topic: create `.claude/rules/<topic>.md` and add one row above. No other file links to a region.
- Every region needs `paths:` frontmatter listing the files it covers. Without it, the file loads every session.
- A rule that prevents real damage goes in `CLAUDE.md`, because that always loads. Regions hold everything else.
- Keep each region under 50 lines. When one grows, condense it or split it, and update this table.
- Keep this file under 30 lines: one row per region, no facts.
