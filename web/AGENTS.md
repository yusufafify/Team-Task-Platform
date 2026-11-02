<!-- intent-skills:start -->
## Skill Loading

Use the repository’s installed Intent. If it is unavailable, report the missing dependency instead of downloading a replacement.
Before editing files for a substantial task:
- Run `npm exec --no -- intent list` from the workspace root to see available local skills.
- If a listed skill matches the task, run `npm exec --no -- intent load <package>#<skill>` before changing files.
- Use the loaded `SKILL.md` guidance while making the change.
- Monorepos: when working across packages, run the skill check from the workspace root and prefer the local skill for the package being changed.
- Multiple matches: prefer the most specific local skill for the package or concern you are changing; load additional skills only when the task spans multiple packages or concerns.
<!-- intent-skills:end -->

# Agent Instructions

This repository is a TanStack Start application in SPA mode, built with Vite, React, and Tailwind CSS v4. As an AI agent working in this repository, you **MUST** adhere to the following rules, architectural patterns, and design principles at all times.

## 1. Agent Workflow (Critical)

1. **Always Use Graphify:** When navigating the codebase or tracing data flow, use `/graphify` or reference `graphify-out/` outputs (`graph.json`, `GRAPH_REPORT.md`) before opening files.
2. **Consult Official Documentation:** Once the `documentation/` directory exists, read the relevant files in it. You must strictly follow these docs, flag any rule violations found within them, and actively keep them up to date with new features or architectural changes.
3. **Progressive Disclosure (Skills & Rules):** Do NOT guess project specifics. Always check for and load relevant domain rules from `.agents/rules/` and `.agents/skills/` before starting a task.

## 2. Modular Rule Index

*When working on specific features, load the corresponding rules from `.agents/rules/`:*
- **Graphify Navigation:** `.agents/rules/graphify.md` (Codebase search and navigation patterns)
- **Documentation Standards:** `.agents/rules/documentation-guidelines.md` (Documentation alignment, updates, and violation flagging)
- **Project Architecture:** `.agents/rules/project-architecture.md` (Vertical Slicing, Feature Colocation, Types, Zod, Error Handling)
- **Design Principles:** `.agents/rules/design-principles.md` (Notion-derived `nesma-design` system, Typography, Dark Mode)
- **Backend Integration:** `.agents/rules/backend-integration.md` (SPA constraints, Mocking)
- **Workflow & Planning:** `.agents/rules/workflow-and-planning.md` (Feature planning, task decomposition, system design)
- **Testing & Implementation:** `.agents/rules/testing-and-implementation.md` (TDD, BDD, incremental changes, SDD)
- **Code Quality & Debugging:** `.agents/rules/code-quality.md` (Code review, simplification, root-cause debugging)
- **Security & Audits:** `.agents/rules/security-guidelines.md` (Security scans, secrets, config audits, hardening)
- **Performance:** `.agents/rules/performance-guidelines.md` (Optimization of frontend and API interactions)
- **Animations:** `.agents/rules/animation-guidelines.md` (GSAP, interactive UI, reduced motion)
- **Moyu Philosophy:** `.agents/rules/moyu-philosophy.md` (Anti-over-engineering, Minimal Edits, SOLID)
- **Real-Time Features:** `.agents/rules/realtime-guidelines.md` (WebSockets, SSE, CRDT, collaboration)
- **Search Systems:** `.agents/rules/search-guidelines.md` (Search engines, indexing, relevance tuning)

*(Note: Each rule explicitly defines which specialized skills you should load when applying it. Always check the rule first!)*
