---
paths:
  - "apps/assistant/retrieval.py"
  - "apps/assistant/management/**"
  - "tests/test_retrieval.py"
---

# Retrieval

Phase 5 RAG: the `search` tool, in `apps/assistant/retrieval.py`. Built from the roadmap line, with no detailed phase prompt. Chatbot flow is in `.claude/rules/assistant.md`.

## How it works

- `search()`: check membership, find what's new or edited, send it with the query in one embedding request, store the vectors, rank what this person may see. Most questions never reach it, because the snapshot answers them.
- It's a tool, not a step before every question, so a snapshot answer spends no embedding request, and the answer cache works as it did. A question that searches isn't cached, like any tool turn.
- `Embedding` holds one vector per task, comment or chat message, and no text. Results are read live from the source, so an edit or a lost permission shows at once.
- `digest` is the MD5 of the model name and the text, compared in SQL, so a status change costs nothing, and a new model re-embeds everything. A comment's text includes its task's title, so a new title re-embeds its comments.
- Scoping: `visible_tasks` for tasks and their comments, `team_messages` for chat, inside the query that ranks, so a member gets nothing of a teammate's. Embedding covers the whole team, whoever searches, because nothing is returned from that step.
- `manage.py embed_pending` catches up every team and is safe to rerun. Run it after the first migration, and after changing `AI_EMBEDDING_MODEL`. It stops with a clear error at a limit, and a rerun carries on.

## Decisions

- Search-time embedding, not `on_commit` (D-017). Nothing on the write path can fail or slow down, and admin edits and seed data can't be missed, because nothing depends on a hook.
- `gemini-embedding-2` at 768 dimensions. In a probe on 2026-11-02, one request held documents and a query, each in its own `Content`, at 718 ms, and an Arabic query matched English text. `gemini-embedding-001` needs two requests, because `task_type` is set per call.
- No vector index, on purpose. An HNSW index filters after ranking, so a member with a narrow view could get few results. Ranking one team's rows is exact, and `team` has an index. Add HNSW with `hnsw.iterative_scan` if a team gets slow.
- A row per source, with no chunking, and text cut at 2000 characters. Long pasted documents are only searchable from the start.
- `BATCH` is 50 because the worst case, 50 texts of 2000 characters, took 1.9 seconds on the free tier (2026-11-02), inside the tool's 8-second timeout. Gemini refuses over 100 in one request with a 400.
- A source deleted while a request is out raises `IntegrityError` at commit. `_store` drops that write, and the next search redoes it.
- The tool's description must say a search covers only what this person may see. Without it, a member was told "Nobody said anything about DNS access" (live, 2026-11-02), which was false: a comment they couldn't see said so. Nothing leaked, and a test for a non-empty reply would have passed.

## Open

- One answer after a search took 15.4 seconds, and that question 21.8, close to the 25-second deadline. Five others with similar results took 0.6 to 1 second, so it looks like Gemini's variance, but the cause wasn't found. A repeat could turn into a 503.
- The free-tier embedding limits aren't published, so `AI_EMBEDDING_REQUESTS_*` defaults are guesses, like the chat ones.
- With a backlog over 50, a search sees only what's embedded so far, until later searches or `embed_pending` reach the rest.
- Several parallel `search` calls in one model turn each spend a request and up to 8 seconds, and nothing caps them but the limits and the question's deadline, checked between rounds.
