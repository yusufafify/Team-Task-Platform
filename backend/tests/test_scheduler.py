import asyncio
import logging
import threading

import pytest
from asgiref.sync import async_to_sync
from django.core.management import CommandError, call_command, get_commands

from config import scheduler


class Stop(Exception):
    """Ends `run_forever` after a set number of ticks."""


@pytest.fixture
def ticks(monkeypatch):
    """Runs the schedule for some hours, recording each job instead of calling it."""
    ran = []
    monkeypatch.setattr(scheduler, "call_command", ran.append)

    def run(hours):
        slept = []

        async def fake_sleep(seconds):
            slept.append(seconds)
            if len(slept) == hours:
                raise Stop

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        with pytest.raises(Stop):
            async_to_sync(scheduler.run_forever)()
        return ran, slept

    return run


def test_every_job_is_a_real_command():
    assert set(scheduler.JOBS) <= set(get_commands())


def test_every_job_runs_at_startup_so_a_restart_cannot_postpone_it_forever(ticks):
    ran, _ = ticks(1)

    assert sorted(ran) == sorted(scheduler.JOBS)


def test_nothing_runs_more_than_hourly_because_neon_must_be_able_to_suspend(ticks):
    _, slept = ticks(2)

    assert slept == [3600, 3600]


def test_daily_jobs_wait_for_their_turn(ticks):
    ran, _ = ticks(25)

    assert ran.count("send_reminders") == 25
    assert ran.count("deliver_pending") == 25
    assert ran.count("generate_reports") == 2
    assert ran.count("flushexpiredtokens") == 2


def test_a_slow_job_cannot_hold_the_thread_socket_logins_wait_on(monkeypatch):
    threads = []
    monkeypatch.setattr(
        scheduler, "call_command", lambda name: threads.append(threading.current_thread())
    )

    async def stop(seconds):
        raise Stop

    monkeypatch.setattr(asyncio, "sleep", stop)

    with pytest.raises(Stop):
        async_to_sync(scheduler.run_forever)()

    assert threading.main_thread() not in threads


def test_a_failed_job_is_logged_and_the_rest_still_run(monkeypatch, caplog):
    ran = []

    def fail_one(name):
        ran.append(name)
        if name == "send_reminders":
            raise CommandError("Stopped")

    monkeypatch.setattr(scheduler, "call_command", fail_one)

    with caplog.at_level(logging.ERROR):
        for name in scheduler.JOBS:
            scheduler._run(name)

    assert ran == list(scheduler.JOBS)
    assert "send_reminders" in caplog.text


def test_run_scheduler_runs_the_same_schedule(monkeypatch):
    calls = []

    async def fake_forever():
        calls.append("ran")

    monkeypatch.setattr(scheduler, "run_forever", fake_forever)

    call_command("run_scheduler")

    assert calls == ["ran"]
