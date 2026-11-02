---
paths:
  - "apps/ai/**"
  - "tests/test_ai.py"
---

# AI

How the LLM is reached. Built from the roadmap line, with no detailed phase prompt. `docs/decisions.md` is outside this agent's edit list, so the choices live here.

## How it works

- `generate()` in `apps/ai/services.py` is the one way to reach the LLM: reserve, send, log. `provider.py` is the only file that imports the SDK. Phases 4 to 6 call `generate()`, never `provider.send`.
- `AICall` is both the log and the limits' counter, so they can't disagree. The row is inserted before sending, under a Postgres advisory lock, so failed and crashed calls count. A row stuck on `pending` means a process died mid-call.
- Never call `generate()` inside `transaction.atomic`: the lock would last the whole request, and a rollback would erase the row, leaving the request uncounted.
- Limits are per minute, per day and per user per day, from environment variables. A day ends at midnight Pacific, when Gemini's quota resets. `user=None`, for reports, skips only the user limit. A refusal is DRF `Throttled` with `wait`, so `Retry-After` reaches clients.
- Gemini's own 429 becomes `Throttled`. Other failures and unfinished replies become `AIUnavailable` (503). Only `completed` and `requires_action` reach the caller, so nothing acts on a truncated answer.
- A tool loop passes the history as a list, then resends `[*history, *reply.steps, function_result]`. Steps go back unchanged, because thought steps carry signatures. `apps/assistant/services.py` is the worked example.
- Tools call the same services as the views, which raise HTTP errors. A tool must catch both `APIException` and `Http404`, because the task and team services use Django's `get_object_or_404`, and must validate ids from the LLM, because that function raises `ValueError` on a non-numeric id.

## Decisions

- Gemini only, through the Interactions API. No fallback provider, because a second provider means a second key and quota nobody asked for. Changing provider means changing `provider.py`.
- Default model `gemini-3.5-flash-lite`, chosen by measuring. On the free tier on 2026-11-02, two runs of the same prompt took 0.7 to 1.6 seconds, against 11 to 19 on `gemini-3.1-flash-lite` and 93 to 106 on `gemini-3.8-flash`, which also used about 15 times the tokens. The network was fine, at 0.4 seconds for HTTPS.
- `TIMEOUT_MS` stays at 25 seconds, under gunicorn's 30, so a slower model needs that limit raised too.
- `store=False`: history lives in Postgres, so Google needn't keep team data. This rules out `previous_interaction_id` and `background=True`.
- The log holds no prompt or reply, so team data stays out of it and out of the admin. It has no purge job, because it grows by at most the daily limit.
- Plain text and `tools` only for now, plus `tool_choice`, which sits inside `generation_config`. Structured output (`response_format`) waits for a caller. `temperature` is deprecated in this API, so don't add it.

## SDK traps (google-genai 2.34.0)

- `HttpRetryOptions` can't disable retries: `attempts=0` is rewritten to 1, and the Interactions path reads that as one retry. The default is 3 retries on 408, 409, 429 and 5xx. `_client()` sets `retry_config = None` instead.
- `automatic_continuation` defaults to on, and each hop is a request nothing counted.
- Interactions errors come from `google.genai._interactions`. `google.genai.errors.APIError` doesn't cover them.
- `test_ai.py` runs the real SDK and fakes only `httpx.HTTPTransport`. Keep it that way: those tests catch an upgrade that brings a trap back.

## Open

- Real free-tier numbers sit behind AI Studio sign-in, so the limit defaults are guesses. The app's limits are a first fence, and Gemini's 429 is the second.
- Free-tier terms: Google may use prompts and replies to improve its products, and human reviewers may read them. The terms say not to send sensitive, confidential or personal information.
- The chatbot and RAG always work from the signed-in user's actual data, on every team. "Seeded data" (user, 2026-11-02) only means test data we generate because no client can create data yet. It is not a restriction, so never gate a feature on it: seeded and real logins run the same flow.
- The terms allow only paid services for clients offered to users in the EEA, Switzerland or the UK.
- Limits are per Google project, so another app on the same project shares the quota and this count can't see it.
- Embeddings aren't built. Phase 5 adds them through the same reserve, send and log path, and they have their own quota, so counts will need to filter by `model`.
