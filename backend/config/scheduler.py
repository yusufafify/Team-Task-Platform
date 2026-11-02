"""The one schedule, run by the server process or by `manage.py run_scheduler`, never both."""

import asyncio
import itertools
import logging

from channels.db import database_sync_to_async
from django.core.management import call_command

logger = logging.getLogger(__name__)

TICK_SECONDS = 3600
# Command: every how many hours. Never tighter than hourly, or Neon can't suspend between runs.
# Each one runs at startup too, because a host that restarts daily would otherwise starve it.
JOBS = {
    "send_reminders": 1,
    "deliver_pending": 1,
    "generate_reports": 24,
    "flushexpiredtokens": 24,
}


def _run(name: str) -> None:
    try:
        call_command(name)
    except Exception:
        # Every job is idempotent, so the next run recovers, and one failure mustn't stop the rest.
        logger.exception("Scheduled job %s failed", name)


async def run_forever() -> None:
    for hour in itertools.count():
        for name, every in JOBS.items():
            if hour % every == 0:
                # Not thread-sensitive: that thread also serves socket logins, and a report is slow.
                await database_sync_to_async(_run, thread_sensitive=False)(name)
        await asyncio.sleep(TICK_SECONDS)
