"""The only module that knows about Gemini. Limits and logging live in services.py."""

from dataclasses import dataclass
from functools import cache

from django.conf import settings
from google import genai
from google.genai import types
from google.genai._interactions import APIError, RateLimitError

# Stays under the 30 seconds that hosts and proxies commonly allow a request.
# Monthly reports may need longer. They run outside a request, so pass `timeout` to send() then.
TIMEOUT_MS = 25_000


class ProviderError(Exception):
    pass


class QuotaExceeded(ProviderError):
    pass


@dataclass(frozen=True)
class Reply:
    status: str
    text: str
    steps: list[dict]
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None


@cache
def _client() -> genai.Client:
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY, http_options=types.HttpOptions(timeout=TIMEOUT_MS)
    )
    # A retry spends scarce quota unseen. HttpRetryOptions can't stop it: attempts=0 retries once.
    client.interactions.sdk_configuration.retry_config = None
    return client


def send(
    prompt: str | list[dict],
    *,
    system: str | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | None = None,
    timeout: float | None = None,
) -> Reply:
    """Make exactly one HTTP request. For a follow-up, pass the history plus `Reply.steps`.

    `timeout` is in seconds, for a caller sharing one deadline across several requests.
    """
    options = {
        "system_instruction": system,
        "tools": tools,
        "generation_config": {"tool_choice": tool_choice} if tool_choice else None,
        "timeout": timeout,
    }
    try:
        interaction = _client().interactions.create(
            model=settings.AI_MODEL,
            input=prompt,
            # History lives in Postgres, so Google needn't keep team data.
            store=False,
            # Each continuation hop would be another request that nothing counted.
            automatic_continuation=False,
            **{name: value for name, value in options.items() if value},
        )
    except RateLimitError as exc:
        raise QuotaExceeded(str(exc)) from exc
    except APIError as exc:
        raise ProviderError(str(exc)) from exc
    usage = interaction.usage
    return Reply(
        status=interaction.status,
        text=interaction.output_text or "",
        steps=[step.model_dump() for step in interaction.steps or []],
        input_tokens=usage.total_input_tokens if usage else None,
        output_tokens=usage.total_output_tokens if usage else None,
        total_tokens=usage.total_tokens if usage else None,
    )
