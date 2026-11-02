# Graph Report - web  (2026-11-03)

## Corpus Check
- 28 files · ~4,906 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 216 nodes · 254 edges · 16 communities (11 shown, 3 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 4 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9cc8f015`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- dependencies
- compilerOptions
- FoundationPage.tsx
- devDependencies
- package.json
- components.json
- utils.ts
- Building For Production
- index.ts
- CLAUDE.md
- Agent Instructions
- __root.tsx
- prettier.config.js
- vite.config.ts

## God Nodes (most connected - your core abstractions)
1. `compilerOptions` - 17 edges
2. `cn()` - 15 edges
3. `scripts` - 8 edges
4. `Building For Production` - 7 edges
5. `tailwind` - 6 edges
6. `aliases` - 6 edges
7. `Button()` - 6 edges
8. `include` - 6 edges
9. `ThemeToggle()` - 5 edges
10. `RouteError()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `getRouter()` --indirect_call--> `RouteError()`  [INFERRED]
  src/router.tsx → src/components/shared/RouteFallbacks.tsx
- `getRouter()` --indirect_call--> `RouteNotFound()`  [INFERRED]
  src/router.tsx → src/components/shared/RouteFallbacks.tsx
- `RouteError()` --calls--> `extractErrorMessage()`  [EXTRACTED]
  src/components/shared/RouteFallbacks.tsx → src/lib/utils.ts
- `Badge()` --calls--> `cn()`  [EXTRACTED]
  src/components/ui/badge.tsx → src/lib/utils.ts
- `Button()` --calls--> `cn()`  [EXTRACTED]
  src/components/ui/button.tsx → src/lib/utils.ts

## Import Cycles
- None detected.

## Communities (16 total, 3 thin omitted)

### Community 0 - "dependencies"
Cohesion: 0.06
Nodes (35): class-variance-authority, clsx, @fontsource-variable/inter, lucide-react, dependencies, class-variance-authority, clsx, @fontsource-variable/inter (+27 more)

### Community 1 - "compilerOptions"
Cohesion: 0.07
Nodes (27): DOM, DOM.Iterable, ES2022, eslint.config.js, prettier.config.js, **/*.ts, **/*.tsx, vite/client (+19 more)

### Community 2 - "FoundationPage.tsx"
Cohesion: 0.15
Nodes (21): applyThemeMode(), getInitialMode(), ThemeMode, ThemeToggle(), toggleMode(), Badge(), badgeVariants, Button() (+13 more)

### Community 3 - "devDependencies"
Cohesion: 0.08
Nodes (25): eslint, devDependencies, eslint, prettier, @tanstack/devtools-vite, @tanstack/eslint-config, @tanstack/react-query-devtools, @tanstack/router-cli (+17 more)

### Community 4 - "package.json"
Cohesion: 0.10
Nodes (19): imports, intent, skills, name, pnpm, onlyBuiltDependencies, private, scripts (+11 more)

### Community 5 - "components.json"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 6 - "utils.ts"
Cohesion: 0.24
Nodes (10): FallbackProps, RouteError(), RouteNotFound(), getContext(), extractErrorMessage(), extractStatusCode(), twMerge, getRouter() (+2 more)

### Community 7 - "Building For Production"
Cohesion: 0.14
Nodes (13): Adding A Route, Adding Links, API Routes, Building For Production, Data Fetching, Getting Started, Learn More, Linting & Formatting (+5 more)

### Community 8 - "index.ts"
Cohesion: 0.31
Nodes (5): BASE_URL, HttpError, FetchOptions, http, request()

### Community 9 - "CLAUDE.md"
Cohesion: 0.25
Nodes (6): Agent Workflow (Critical), Architecture, Commands, Communication Style, graphify, Modular Rule Index

### Community 10 - "Agent Instructions"
Cohesion: 0.40
Nodes (4): 1. Agent Workflow (Critical), 2. Modular Rule Index, Agent Instructions, Skill Loading

## Knowledge Gaps
- **114 isolated node(s):** `$schema`, `style`, `rsc`, `tsx`, `config` (+109 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 123 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `dependencies` connect `dependencies` to `package.json`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Why does `devDependencies` connect `devDependencies` to `package.json`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **What connects `$schema`, `style`, `rsc` to the rest of the system?**
  _114 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.05714285714285714 - nodes in this community are weakly interconnected._
- **Should `compilerOptions` be split into smaller, more focused modules?**
  _Cohesion score 0.07142857142857142 - nodes in this community are weakly interconnected._
- **Should `FoundationPage.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.14814814814814814 - nodes in this community are weakly interconnected._
- **Should `devDependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._