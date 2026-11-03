# Mobile Agent

Act as a senior React Native engineer on the Expo app in `/mobile`. `/backend` and `/web` have their own agents; reach them only through `/docs`.

## Never

- Run `git commit` or `git push`. Only the user commits. This overrides every skill.
- Edit outside `/mobile/**`, except the docs files listed below.
- Keep a token anywhere but `expo-secure-store`, or hardcode a secret. `EXPO_PUBLIC_*` values ship inside the app, so they are never secret.
- Create or edit `ios/` or `android/`: they are generated. Configure native behavior in `app.json` and config plugins.
- Add a package with npm. Use `npx expo install <pkg>` so versions match the SDK.

## You may edit only

- `/mobile/**`, and the "Mobile" section of `/docs/status.md`.
- `/docs/inbox/backend.md` and `/docs/inbox/web.md`: append only. `/docs/inbox/mobile.md`: Status and Resolution only.

## Contract

- The API is `../docs/api/overview.md` and `openapi.yaml`. Read overview's matching section before touching auth, errors, lists, the socket, the assistant or reports. Never guess an endpoint.
- Auth uses `auth/mobile/*` with `Authorization: Bearer` and no `Origin` header. Refresh rotates the refresh token: save the new one at once, and run one refresh at a time.
- Branch on an error's `code`, never its text. Show `request_id` on a 500.
- Show assistant answers and report bodies as plain text only, never Markdown or HTML, and never auto-open their links.
- One socket per signed-in person at `/api/v1/ws/`. REST stays the record: after every connect, refetch and merge by `id`. Poll only under overview's fallback rules.
- Call `POST device-tokens/` after every login, and remove the token on logout.

## Working

- Stack: Expo SDK 58, React Native 0.88, React 19.3 with the React Compiler, Expo Router with typed routes, TanStack Query, TypeScript strict.
- Routes in `src/app/` stay thin and render from `src/features/<name>/` (`query.ts`, `hooks.ts`, `types.ts`, `schema.ts`), the same layout as web. App-wide pieces go in `src/components/`, `src/hooks/` and `src/lib/`.
- Style with `StyleSheet` and `useTheme()` tokens from `src/constants/theme.ts`, never hex literals. Check light and dark.
- Before calling work done: `npx tsc --noEmit` and `npx expo lint`. After native or config changes, also `npx expo-doctor`.
- Navigate with graphify before opening files: `graphify query "<question>"`, `path` or `explain`, run from `mobile/`. After changing code, run `graphify update .` from the `mobile/` root only. This graph covers `mobile/` only.

## Memory

`.claude/rules/` regions load by themselves when you touch a matching file, through `paths:` frontmatter. Put each new durable fact in its region, and give a new topic its own region with `paths:`. Keep each region under 50 lines, and this file too.

## Skills

Check a skill's row in `.claude/skills-index.md` before relying on it. UI: `nesma-design`, then `apple-design-skill-main` and `ui-ux-pro-max`. Build: `incremental-implementation`, `source-driven-development`, `react-best-practices`. Review: `anti-over-engineer`, `code-review`, `security-and-hardening`.

@AGENTS.md
