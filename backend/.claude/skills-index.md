# Skills Index

Read on demand. Don't import this file.

Populated by /sync-skills. Last synced 2026-11-01: 35 usable.

Load a skill only when its row applies. Most skill examples are TypeScript, so translate them to Django rather than copying them. The `software-*` skills link to other skills and a Learnings Loop script that aren't installed here; skip those links.

| Skill | What it covers | When to use it in THIS project | Ignore |
|---|---|---|---|
| anti-over-engineer (`moyu-en`) | Scope control and restraint | Before delivering any diff | "No `services/`", "no tests or type hints unless asked": `CLAUDE.md` requires all three. The PUA section |
| cdrf-expert | DRF class-based view internals, MRO, override hooks | Choosing views and hooks in Phase 2. We run DRF 3.18.3 | Putting logic in `perform_create`-style hooks: they call a service |
| code-review | General review checklist and smell thresholds | Reviewing non-Django files such as workflows | Review metrics and `github-agile`. Use django-reviewer for Django code |
| code-simplification | Behavior-preserving cleanup | After a phase's tests pass | TypeScript and React sections |
| context-engineering | Rules files and context loading | When output quality drops | Its `CLAUDE.md` template and MCP list: brain and handover already cover this |
| database-deletion-strategy | Per-table deletion tiers | Every model's `on_delete` in Phase 1, and any delete endpoint | Prisma, TypeORM, SQLAlchemy, Hibernate and Drizzle notes. Raw SQL: use Django `on_delete` and services |
| debugging-and-error-recovery | Root-cause triage | Any failing test or unexpected error, using `uv run pytest` | npm commands. "Safe Fallback Patterns" |
| dependency-scan | CVE checks across package managers | Before release. `pip-audit` isn't installed yet; add it with `uv add --dev` | `--fix`, `git add .`, bare `pip`, other ecosystems |
| django-expert | Django and DRF patterns, with large references | Phases 1, 2 and 7. Load only the reference the task needs | Redis, Memcached and Celery content |
| django-reviewer | Review of Django and Python changes | After every Django change, as the default reviewer. Report-only unless asked to edit | "Type hints only where already used": services require them |
| django-safe-migration | Zero-downtime PostgreSQL migrations | Any migration on a deployed table. Settings are in `CLAUDE.md` | Rewrites of Phase 1 initial migrations: those tables are new and empty |
| email-best-practices | Deliverability, transactional email, compliance, webhooks, accessibility | Phase 8 | Marketing, email capture and list-management content |
| gemini-api-dev | Gemini SDK (`google-genai`), Interactions API, function calling, structured output, streaming, embeddings | Phases 3 to 6. Fetch the matching docs page before writing code. `uv add google-genai` arrives with Phase 3 | TypeScript examples, `pip install`, image, video, speech and music generation, Live API |
| idea-refine | Structured ideation | Only when the user asks to explore an idea | Its `docs/ideas/` output and setup script |
| incremental-implementation | Thin, verified slices | Multi-file work in every phase | UI slices, feature flags, the missing `definition-of-done.md` |
| performance-optimization | Measure-first tuning: N+1, query plans, cache design | A measured slowdown, or checking list endpoints for N+1 | Frontend and Core Web Vitals content. The Redis row |
| planning-and-task-breakdown | Task lists with acceptance criteria | Splitting a phase prompt into steps | `tasks/plan.md` and `tasks/todo.md`: use `handover.md`. UI slices |
| resend | Resend API usage and gotchas | Phase 8, when `uv add resend` arrives. Use its Python examples | Node.js examples, inbound, broadcasts, automations, inboxes, `agent-email-inbox` |
| security-and-hardening | OWASP prevention, privacy, LLM security | Phases 2, 4 and 8 | Express, helmet, zod and bcrypt examples: use Django and DRF equivalents |
| security-scan | Vulnerability scan checklist | Before release, and after auth or AI work | `--fix`, `/secrets-scan`, `/config-scan` (not installed) |
| software-ai-integration | LLM patterns: tools, structured output, guardrails, cost | Phases 3, 4 and 6 | Vercel AI SDK, Zod, React hooks, CopilotKit, LangGraph, CrewAI, gateways |
| software-backend | API, data and reliability defaults | Phases 2 and 8 | FastAPI, SQLAlchemy, other-language templates, queues, dead-letter queues, OpenTelemetry |
| software-clean-code-standard | `CC-*` rule IDs | Citing rules in reviews | Overlays and waiver process: there's one reviewer, not a team |
| software-code-review | Severity rubric and AI-generated code checks | Phase-end review of large diffs, using P0 to P3 | Frontend, mobile, blockchain and ML overlays. Tool comparisons |
| software-performance | Profiling, load tests, budgets | Only when latency is a stated problem | Lighthouse and frontend budgets |
| software-realtime | Transport choice, reconnects, presence | Team chat and notifications design in Phase 2 | Redis, NATS, Kafka, CRDTs, PartyKit, multi-node scaling |
| software-search | Postgres search, pgvector, hybrid ranking | Phase 5 | Algolia, Elasticsearch, Typesense, Meilisearch, facets, search analytics |
| software-security-appsec | Auth, input handling, supply chain, agent threat models | Phases 2 and 4 | Web3 and .NET content. "Avoid JWTs": see below |
| solid | SOLID, clean code, TDD | Design questions about a service's responsibilities | Mandatory value objects, two-field classes, 10-line methods, one-dot rule: they don't fit Django models |
| source-driven-development | Verifying code against official docs | Framework code you'd otherwise write from memory. Use `docs.djangoproject.com/en/5.2/`, not its 6.0 example | Source citations in code comments, unless they explain a non-obvious why |
| spec-driven-development | Specs before code | When a phase prompt leaves requirements unclear | `SPEC-*.md` and `tasks/`: the phase prompt is the spec |
| sql-expert | Complex SQL, window functions, indexes | Stats and report queries the ORM can't express cleanly | `pip install`, psycopg2, SQLAlchemy, other dialects, its migration section (`UPDATE ... LIMIT` isn't valid PostgreSQL) |
| system-design | Architecture trade-offs for solo developers | Hard-to-reverse choices such as chat transport or hosting | `docs/design/`, `adr/`, `context/output-config.md`: decisions belong in `/docs/decisions.md` |
| task-decomposition | Sizing and splitting oversized work | When a step is too big to estimate | Story points and `github-agile` |
| test-driven-development | Red-green tests, test pyramid, bug reproduction | Service logic and every bug fix, using `uv run pytest` | Browser and DevTools sections. Spawning a subagent for tests |

## Conflicts with the Architecture decisions

The Architecture section of `CLAUDE.md` wins over every skill.

| Skill guidance | Decision | Do this instead |
|---|---|---|
| django-expert references: "Use Redis for production caching", "Offload heavy tasks to Celery" | D-002 | Database cache; idempotent management commands |
| software-backend, including `references/message-queues-background-jobs.md`: queues, workers, dead-letter queues | D-002, D-015 | Management commands run by `run_scheduler` |
| software-realtime: Redis pub/sub, Redis `SETEX` presence, Kafka | D-002 | Design for one node without a broker; choose the transport in Phase 2 |
| performance-optimization: shared Redis or Memcached cache | D-002 | Database cache |
| software-ai-integration: LangGraph, queue-and-worker batches, background re-index jobs | D-002, D-003 | Direct provider SDK; management commands for batches; `transaction.on_commit` for re-embedding |
| software-ai-integration: retry on schema failure, regenerate, semantic cache lookups | D-006 | Put more context in one request; use an exact-match answer cache; count every extra call against the request budget |
| anti-over-engineer: `services/` listed as over-engineering, "code lives where it's used" | D-001 | Keep business logic in `services.py` |
| django-expert and django-reviewer: domain logic in models or managers | D-001 | Keep business logic in `services.py` |
| database-deletion-strategy: cron or worker purge jobs, row-level security | D-002, D-004 | Idempotent management command; role and team scoping in Python |
| resend automations, email-best-practices list hygiene jobs | D-002 | Keep workflow logic in Django; run it through management commands |
| email-best-practices references: job queue for webhook handling and critical sends | D-002, D-003 | Send through `transaction.on_commit`; keep pending work in a Postgres table processed by a management command. Scalability: this is deliberately simple, so retries wait for the next scheduler run; if we need to scale, optimize that timing then |
| debugging-and-error-recovery: default value when config is missing | D-007 | Keep failing at startup in prod |
| sql-expert and software-backend: raw SQL or bypassing the ORM | D-004, D-005 | Allowed for developers only; scope by role and team in Python, and never expose it to the LLM |
| gemini-api-dev: managed agents, Deep Research, code execution, Google Search, URL context, computer use, hosted File Search | D-004, D-005 | Give the model only typed function tools over scoped Django services; use pgvector for RAG |
| gemini-api-dev: `background=True` with a polling loop | D-002 | Make a single call from a service or management command |

## Conflicts with the stack and conventions

These aren't Architecture decisions, but the project's choices still win.

- software-security-appsec and security-and-hardening prefer server sessions and warn against JWTs. The stack uses simplejwt. How the web app stores tokens is a Phase 2 decision.
- software-backend wants RFC 9457 error bodies, which DRF doesn't produce by default. Decide the error format in Phase 2 and publish it through the changelog.
- anti-over-engineer says no tests unless asked; solid and test-driven-development make them mandatory. Follow "Testing" in `CLAUDE.md`.
- gemini-api-dev says Google stores interactions by default (55 days on paid, 1 day on free), and `store=False` disables `previous_interaction_id`. Keep conversation history in Postgres and decide `store` in Phase 3.
