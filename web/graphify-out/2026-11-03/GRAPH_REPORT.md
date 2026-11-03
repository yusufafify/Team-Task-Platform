# Graph Report - web  (2026-11-03)

## Corpus Check
- 104 files · ~18,217 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 563 nodes · 1345 edges · 20 communities (15 shown, 3 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `703580cf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- dependencies
- compilerOptions
- TaskFormDialog.tsx
- devDependencies
- format.ts
- components.json
- utils.ts
- Building For Production
- TaskPage.tsx
- CLAUDE.md
- Agent Instructions
- __root.tsx
- prettier.config.js
- vite.config.ts
- MembersPage.tsx
- auth/query.ts
- StatsPage.tsx
- ThemeToggle.tsx

## God Nodes (most connected - your core abstractions)
1. `cn()` - 39 edges
2. `Button()` - 25 edges
3. `useSchemaForm()` - 18 edges
4. `extractErrorMessage()` - 18 edges
5. `displayName()` - 17 edges
6. `compilerOptions` - 17 edges
7. `useTeams()` - 15 edges
8. `ErrorState()` - 13 edges
9. `User` - 13 edges
10. `FormError()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `confirm()` --calls--> `extractErrorMessage()`  [EXTRACTED]
  src/components/shared/ConfirmDialog.tsx → src/lib/utils.ts
- `BoardSkeleton()` --calls--> `cn()`  [EXTRACTED]
  src/features/tasks/TaskBoard.tsx → src/lib/utils.ts
- `RouteError()` --calls--> `extractErrorMessage()`  [EXTRACTED]
  src/components/shared/RouteFallbacks.tsx → src/lib/utils.ts
- `getRouter()` --indirect_call--> `RouteError()`  [INFERRED]
  src/router.tsx → src/components/shared/RouteFallbacks.tsx
- `getRouter()` --indirect_call--> `RouteNotFound()`  [INFERRED]
  src/router.tsx → src/components/shared/RouteFallbacks.tsx

## Import Cycles
- None detected.

## Communities (20 total, 3 thin omitted)

### Community 0 - "dependencies"
Cohesion: 0.06
Nodes (35): class-variance-authority, clsx, @fontsource-variable/inter, lucide-react, dependencies, class-variance-authority, clsx, @fontsource-variable/inter (+27 more)

### Community 1 - "compilerOptions"
Cohesion: 0.07
Nodes (27): DOM, DOM.Iterable, ES2022, eslint.config.js, prettier.config.js, **/*.ts, **/*.tsx, vite/client (+19 more)

### Community 2 - "TaskFormDialog.tsx"
Cohesion: 0.07
Nodes (50): ComposerProps, ConfirmDialogProps, Page(), PageProps, EmptyState(), Button(), buttonVariants, Card() (+42 more)

### Community 3 - "devDependencies"
Cohesion: 0.04
Nodes (44): eslint, devDependencies, eslint, prettier, @tanstack/devtools-vite, @tanstack/eslint-config, @tanstack/react-query-devtools, @tanstack/router-cli (+36 more)

### Community 4 - "format.ts"
Cohesion: 0.06
Nodes (44): Composer(), AssistantPage(), AssistantPageProps, describeAskError(), formatWait(), threadQuery(), useAskAssistant(), useAssistantThread() (+36 more)

### Community 5 - "components.json"
Cohesion: 0.11
Nodes (17): aliases, components, hooks, lib, ui, utils, iconLibrary, rsc (+9 more)

### Community 6 - "utils.ts"
Cohesion: 0.08
Nodes (38): FallbackProps, RouteError(), RouteNotFound(), EmptyStateProps, ErrorState(), ErrorStateProps, applyEvent(), catchUp() (+30 more)

### Community 7 - "Building For Production"
Cohesion: 0.14
Nodes (13): Adding A Route, Adding Links, API Routes, Building For Production, Data Fetching, Getting Started, Learn More, Linting & Formatting (+5 more)

### Community 8 - "TaskPage.tsx"
Cohesion: 0.06
Nodes (49): Badge(), badgeVariants, PRIORITY_BADGES, PRIORITY_LABELS, STATUS_LABELS, commentsQuery(), TASK_PAGE_SIZE, taskQuery() (+41 more)

### Community 9 - "CLAUDE.md"
Cohesion: 0.25
Nodes (6): Agent Workflow (Critical), Architecture, Commands, Communication Style, graphify, Modular Rule Index

### Community 10 - "Agent Instructions"
Cohesion: 0.40
Nodes (4): 1. Agent Workflow (Critical), 2. Modular Rule Index, Agent Instructions, Skill Loading

### Community 16 - "MembersPage.tsx"
Cohesion: 0.07
Nodes (41): ConfirmDialog(), confirm(), TaskFields(), AddMemberForm(), AddMemberFormProps, MemberRow(), MemberRowProps, MembersPage() (+33 more)

### Community 17 - "auth/query.ts"
Cohesion: 0.10
Nodes (32): AccountPage(), AuthLayout(), STICKY_NOTES, LOGIN_MESSAGES, useLoginForm(), useRegisterForm(), useSignIn(), signIn() (+24 more)

### Community 18 - "StatsPage.tsx"
Cohesion: 0.11
Nodes (24): Skeleton(), useReports(), ReportsPage(), ReportsPageProps, MonthlyReport, useTeamStats(), statsSearchSchema, formatDelay() (+16 more)

### Community 19 - "ThemeToggle.tsx"
Cohesion: 0.53
Nodes (5): applyThemeMode(), getInitialMode(), ThemeMode, ThemeToggle(), toggleMode()

## Knowledge Gaps
- **156 isolated node(s):** `$schema`, `style`, `rsc`, `tsx`, `config` (+151 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 189 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Button()` connect `TaskFormDialog.tsx` to `format.ts`, `utils.ts`, `TaskPage.tsx`, `MembersPage.tsx`, `auth/query.ts`, `StatsPage.tsx`, `ThemeToggle.tsx`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `cn()` connect `TaskFormDialog.tsx` to `format.ts`, `utils.ts`, `TaskPage.tsx`, `auth/query.ts`, `StatsPage.tsx`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `dependencies` connect `dependencies` to `devDependencies`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **What connects `$schema`, `style`, `rsc` to the rest of the system?**
  _156 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.05714285714285714 - nodes in this community are weakly interconnected._
- **Should `compilerOptions` be split into smaller, more focused modules?**
  _Cohesion score 0.07142857142857142 - nodes in this community are weakly interconnected._
- **Should `TaskFormDialog.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06693306693306693 - nodes in this community are weakly interconnected._