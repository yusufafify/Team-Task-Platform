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

No test runner is configured. Verify a change with `tsc`, `lint`, `check` and `build`. The pure thread-merge logic has a Node test: `node --experimental-strip-types --test src/lib/pagination.test.ts`.

The dev server proxies `/api` (and the socket) to `http://localhost:8000`, as the web host does in prod for `/api` but not the socket, so leave `VITE_API_URL` empty. The API only allows the origin `http://localhost:3000`: if Vite falls back to another port because 3000 is taken, every write gets 403.

A running `preview` server keeps linking the previous build's hashed assets, so after a rebuild the page renders unstyled until it is restarted.

## Architecture

**SPA on Start.** `vite.config.ts` sets `tanstackStart({ spa: { enabled: true } })`. There is no `index.html` or `main.tsx`: the document is the `shellComponent` in `src/routes/__root.tsx`, prerendered at build time to `dist/client/_shell.html`. Deploy `dist/client` to a static host that falls back to `_shell.html` for every path. On Vercel, `vercel.json` does this (project `nesma-airlines`, Root Directory `web`), and a push to `main` deploys production, so the CLI can't deploy from `web/`. Its `/api/` proxy rule must use the form `/api/(.*)`, because `/api/:path*` 404s on trailing slashes, and Vercel rewrites drop WebSocket upgrades. Nothing may need a server at runtime, so `createServerFn` and `useSession` are off limits, even for mocks.

**Data flow.** Route file → feature component → `query.ts` hook → `http` facade (`src/lib/http/fetch_instance`) → backend at `/api/v1/`, on `VITE_API_URL` if set. Endpoints are relative, such as `http.get('tasks/')`. The facade sends cookies on every request, times out reads after 30s but never writes, and throws `HttpError` (`status`, `data`, `code`, `requestId`, `retryAfter`). Read errors through the `extract*` helpers in `src/lib/utils.ts`, and branch on the code, never the message. On a stale-session 401 it runs one shared refresh and retries once; `QueryCache` and `MutationCache` in `root-provider.tsx` send a session that stays dead to `/login`. The contract is `../docs/api/overview.md`.

**Live updates.** `useLiveSocket` in `src/features/live/hooks.ts` holds the one socket, mounted by `AppShell`. REST stays the record: every connect fetches the open chat's first page and the unread count, and threads merge by `id` through `src/lib/pagination.ts`. Polling exists only as the contract's fallback while the socket is down.

**Router and query wiring.** `getContext()` in `src/integrations/tanstack-query/root-provider.tsx` creates the `QueryClient` (retries 5xx and network failures only). `src/router.tsx` passes it into router context, so loaders reach it as `context.queryClient`. Failing routes and unknown paths render `src/components/shared/RouteFallbacks.tsx` in place. Throw `notFound()` from a loader, never during render: only a route with its own `notFoundComponent` catches one thrown in render, and otherwise the whole shell is lost. `/_app` guards signed-in pages and `/_auth` holds login and register. `src/routeTree.gen.ts` is generated; never edit it.

**Feature layout.** Routes in `src/routes/` stay thin and render from `src/features/<name>/`, which holds `query.ts`, `hooks.ts`, `types.ts`, `schema.ts` and `mocks/`. `src/components/ui/` is for shared primitives only, and `src/components/shared/` for app-wide pieces such as `Page`, `States`, `ConfirmDialog` and `Composer`. Forms use `useSchemaForm` in `src/hooks/`, which validates with Zod and maps the API's 400 field errors onto the fields.

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
