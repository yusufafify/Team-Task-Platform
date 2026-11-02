# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Nesma Airlines web frontend: a client-only SPA on TanStack Start, with Vite, React 19 and Tailwind CSS v4. It is the `web/` package of the monorepo. The backend is a separate project in `../backend`, reached only over HTTP.

## Communication Style

- **Be concise:** get straight to the point and skip conversational filler.

## Commands

Run from `web/`. The package manager is npm.

```bash
npm run dev              # Dev server on http://localhost:3000
npm run build            # Production build into dist/ (does not typecheck)
npm run preview          # Serve the build; restart it after every rebuild
npx tsc --noEmit         # Typecheck
npm run lint             # ESLint
npm run check            # Prettier check
npm run format           # Prettier write, then ESLint fix
npm run generate-routes  # Regenerate src/routeTree.gen.ts by hand
npx shadcn@latest add <component>  # Add a primitive, then restyle it to the tokens
```

No test runner is configured, so there is no test command yet. Verify a change with `tsc`, `lint`, `check` and `build`.

A running `preview` server keeps linking the previous build's hashed assets, so after a rebuild the page renders unstyled until it is restarted.

## Architecture

**SPA on Start.** `vite.config.ts` sets `tanstackStart({ spa: { enabled: true } })`. There is no `index.html` or `main.tsx`: the document is the `shellComponent` in `src/routes/__root.tsx`, prerendered at build time to `dist/client/_shell.html`. Deploy `dist/client` to a static host that falls back to `_shell.html` for every path. Nothing may need a server at runtime, so `createServerFn` and `useSession` are off limits, even for mocks.

**Data flow.** Route file → feature component → `query.ts` hook → `http` facade (`src/lib/http/fetch_instance`) → backend at `VITE_API_URL`. The facade sends cookies on every request, times out reads after 30s but never writes, and throws `HttpError` (`status`, `data`). Read errors through `extractStatusCode` and `extractErrorMessage` in `src/lib/utils.ts`. It has no auth handling yet: there is no 401 refresh or redirect, because that depends on the backend's contract.

**Router and query wiring.** `getContext()` in `src/integrations/tanstack-query/root-provider.tsx` creates the `QueryClient` (retries 5xx and network failures only). `src/router.tsx` passes it into router context, so loaders reach it as `context.queryClient`. Failing routes and unknown paths render `src/components/shared/RouteFallbacks.tsx` in place. `src/routeTree.gen.ts` is generated; never edit it.

**Feature layout.** Routes in `src/routes/` stay thin and render from `src/features/<name>/`, which holds `query.ts`, `hooks.ts`, `types.ts`, `schema.ts` and `mocks/`. `src/components/ui/` is for shared primitives only. `src/features/foundation/` is the placeholder page at `/`; delete it when the real home lands.

**Styling.** `src/styles.css` holds every token: fixed values in `@theme`, theme-dependent ones as variables under `:root` and `.dark`, mapped to Tailwind through `@theme inline`. Any new custom `text-*`, `shadow-*` or spacing token must also be registered in `extendTailwindMerge` in `src/lib/utils.ts`, or `cn()` will merge it wrongly. `THEME_INIT_SCRIPT` in `__root.tsx` sets `.dark` before first paint, and `ThemeToggle` persists the choice to `localStorage.theme`. `@/` and `#/` both alias `src/`; use `@/`.

## Agent Workflow (Critical)

1. **Always use Graphify:** when navigating the codebase or tracing data flow, query `graphify-out/` before opening files, and refresh it after code changes. See `.claude/rules/graphify.md`.
2. **Load rules and skills first:** do not guess project specifics. Check `.claude/rules/` and `.claude/skills/` before starting a task; each rule names the skills to load with it.
3. **Keep guides current:** follow `documentation/` once it exists, flag anything in it that breaks these rules, and update it when you add a concept others must know.
4. **Intent:** `AGENTS.md` asks for Intent-based skill loading, but Intent is not installed, so `npm exec --no -- intent list` fails. Report that rather than downloading a replacement.

## Modular Rule Index

Load the matching rule from `.claude/rules/` when working in its area:

- **Graphify Navigation:** `graphify.md` (codebase search and navigation)
- **Documentation Standards:** `documentation-guidelines.md` (alignment, updates, flagging violations)
- **Project Architecture:** `project-architecture.md` (vertical slicing, colocation, types, Zod, error handling)
- **Design Principles:** `design-principles.md`. **Mandatory for any UI/UX work, including every new feature:** load `nesma-design` (source of truth, adapted from Notion) plus `anti-over-engineer`, `ui-ux-pro-max`, `taste-skill`, `apple-design-skill-main`, `frontend-design`.
- **Backend Integration:** `backend-integration.md` (SPA constraints, mocking)
- **Workflow & Planning:** `workflow-and-planning.md` (feature planning, task decomposition, system design)
- **Testing & Implementation:** `testing-and-implementation.md` (TDD, BDD, incremental changes, SDD)
- **Code Quality & Debugging:** `code-quality.md` (review, simplification, root-cause debugging)
- **Security & Audits:** `security-guidelines.md` (scans, secrets, config audits, hardening)
- **Performance:** `performance-guidelines.md` (frontend and API optimization)
- **Animations:** `animation-guidelines.md` (GSAP, interactive UI, reduced motion)
- **Moyu Philosophy:** `moyu-philosophy.md` (anti-over-engineering, minimal edits, SOLID)
- **Real-Time Features:** `realtime-guidelines.md` (WebSockets, SSE, CRDT, collaboration)
- **Search Systems:** `search-guidelines.md` (engines, indexing, relevance tuning)

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:

- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` from the `web/` root to keep the graph current (AST-only, no API cost). Running it from a subfolder leaves a stray `graphify-out/` there.
