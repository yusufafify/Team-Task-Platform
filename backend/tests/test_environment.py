"""`.env` alone chooses the settings module, at every entry point."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
PRINT_MODULE = "from django.conf import settings; print(settings.SETTINGS_MODULE)"
MANAGE = ["manage.py", "shell", "-v", "0", "-c", PRINT_MODULE]
WSGI = ["-c", f"import config.wsgi; {PRINT_MODULE}"]
ASGI = ["-c", f"import config.asgi; {PRINT_MODULE}"]
PROD_VALUES = """
DJANGO_SECRET_KEY=test-only
DJANGO_ALLOWED_HOSTS=example.com
DJANGO_NUM_PROXIES=2
DATABASE_URL=postgres://localhost:5432/test
CORS_ALLOWED_ORIGINS=https://example.com
GEMINI_API_KEY=test-only
"""


def run_with_env_file(tmp_path: Path, env_file: str, args: list[str]):
    shutil.copy(BACKEND / "manage.py", tmp_path)
    for package in ("config", "apps"):
        shutil.copytree(
            BACKEND / package, tmp_path / package, ignore=shutil.ignore_patterns("__pycache__")
        )
    (tmp_path / ".env").write_text(env_file)
    # The test process already holds these from pytest-django and the real .env, and they'd win.
    hidden = {
        "DJANGO_SETTINGS_MODULE",
        "DJANGO_NUM_PROXIES",
        "DATABASE_URL",
        "DIRECT_URL",
        "TEST_DATABASE_URL",
        "GEMINI_API_KEY",
    }
    env = {k: v for k, v in os.environ.items() if k not in hidden}
    return subprocess.run(
        [sys.executable, *args], cwd=tmp_path, env=env, capture_output=True, text=True
    )


@pytest.mark.parametrize(
    ("args", "module"),
    [
        (MANAGE, "config.settings.prod"),
        (WSGI, "config.settings.dev"),
        (ASGI, "config.settings.dev"),
    ],
)
def test_env_file_chooses_settings_module(tmp_path, args, module):
    result = run_with_env_file(tmp_path, f"DJANGO_SETTINGS_MODULE={module}{PROD_VALUES}", args)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == module


@pytest.mark.parametrize("args", [MANAGE, WSGI, ASGI])
def test_missing_settings_module_refuses_to_start(tmp_path, args):
    result = run_with_env_file(tmp_path, PROD_VALUES, args)

    assert result.returncode != 0
    assert "DJANGO_SETTINGS_MODULE" in result.stderr


def test_test_settings_require_their_own_database(tmp_path):
    env_file = (
        "DJANGO_SETTINGS_MODULE=config.settings.test\nDATABASE_URL=postgres://u:p@ep-main/neondb\n"
    )

    result = run_with_env_file(tmp_path, env_file, MANAGE)

    assert result.returncode != 0
    assert "TEST_DATABASE_URL" in result.stderr


@pytest.mark.parametrize(
    ("main", "test"),
    [
        ("ep-main", "ep-main"),
        ("ep-main", "ep-main-pooler"),
        ("ep-main-pooler", "ep-main"),
    ],
)
def test_test_settings_refuse_the_main_database(tmp_path, main, test):
    env_file = (
        "DJANGO_SETTINGS_MODULE=config.settings.test\n"
        f"DATABASE_URL=postgres://u:p@{main}/neondb\n"
        f"TEST_DATABASE_URL=postgres://u:p@{test}/neondb\n"
    )

    result = run_with_env_file(tmp_path, env_file, MANAGE)

    assert result.returncode != 0
    assert "must not share an endpoint with DATABASE_URL" in result.stderr


def test_test_settings_refuse_a_pooled_host(tmp_path):
    env_file = (
        "DJANGO_SETTINGS_MODULE=config.settings.test\n"
        "DATABASE_URL=postgres://u:p@ep-dev/neondb\n"
        "TEST_DATABASE_URL=postgres://u:p@ep-test-pooler/neondb\n"
    )

    result = run_with_env_file(tmp_path, env_file, MANAGE)

    assert result.returncode != 0
    assert "must use the direct host" in result.stderr


def test_test_settings_accept_a_local_database_when_database_url_is_unset(tmp_path):
    env_file = (
        "DJANGO_SETTINGS_MODULE=config.settings.test\n"
        "TEST_DATABASE_URL=postgres://u:p@localhost:5432/ci\n"
    )

    result = run_with_env_file(tmp_path, env_file, MANAGE)

    assert result.returncode == 0, result.stderr


def test_pytest_ignores_a_settings_variable_in_the_shell():
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": "config.settings.dev"}

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "tests/test_smoke.py"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
    )

    assert "settings: config.settings.test (from option)" in result.stdout


def test_migrate_connects_through_direct_url(tmp_path):
    env_file = (
        "DJANGO_SETTINGS_MODULE=config.settings.dev\n"
        "DATABASE_URL=postgres://u:p@pooled.invalid/db\n"
        "DIRECT_URL=postgres://u:p@direct.invalid/db\n"
    )

    result = run_with_env_file(tmp_path, env_file, ["manage.py", "migrate"])

    assert "direct.invalid" in result.stderr
    assert "pooled.invalid" not in result.stderr


def test_migrate_falls_back_to_database_url(tmp_path):
    env_file = (
        "DJANGO_SETTINGS_MODULE=config.settings.dev\n"
        "DATABASE_URL=postgres://u:p@pooled.invalid/db\n"
    )

    result = run_with_env_file(tmp_path, env_file, ["manage.py", "migrate"])

    assert "pooled.invalid" in result.stderr


def test_other_commands_stay_on_the_pooled_url(tmp_path):
    env_file = (
        "DJANGO_SETTINGS_MODULE=config.settings.dev\n"
        "DATABASE_URL=postgres://u:p@pooled.invalid/db\n"
        "DIRECT_URL=postgres://u:p@direct.invalid/db\n"
    )
    print_host = "from django.conf import settings; print(settings.DATABASES['default']['HOST'])"
    args = ["manage.py", "shell", "-v", "0", "-c", print_host]

    result = run_with_env_file(tmp_path, env_file, args)

    assert result.stdout.strip() == "pooled.invalid"


def test_prod_logs_errors_to_the_console(tmp_path):
    env_file = f"DJANGO_SETTINGS_MODULE=config.settings.prod{PROD_VALUES}"
    log_error = "import logging; logging.getLogger('django.request').error('probe-error')"
    args = ["manage.py", "shell", "-v", "0", "-c", log_error]

    result = run_with_env_file(tmp_path, env_file, args)

    # Outside a request the ID is "-", and the format must still work.
    assert re.search(r"\d{4}-\d\d-\d\d \S+ ERROR django\.request \[-\] probe-error", result.stderr)


def test_prod_takes_its_proxy_count_from_the_environment(tmp_path):
    env_file = f"DJANGO_SETTINGS_MODULE=config.settings.prod{PROD_VALUES}"
    print_proxies = "from rest_framework.settings import api_settings as s; print(s.NUM_PROXIES)"
    args = ["manage.py", "shell", "-v", "0", "-c", print_proxies]

    result = run_with_env_file(tmp_path, env_file, args)

    assert result.stdout.strip() == "2"


def test_prod_marks_auth_cookies_secure(tmp_path):
    env_file = f"DJANGO_SETTINGS_MODULE=config.settings.prod{PROD_VALUES}"
    print_flag = "from django.conf import settings; print(settings.AUTH_COOKIE_SECURE)"
    args = ["manage.py", "shell", "-v", "0", "-c", print_flag]

    result = run_with_env_file(tmp_path, env_file, args)

    assert result.stdout.strip() == "True"


def test_prod_refuses_to_start_without_a_proxy_count(tmp_path):
    values = PROD_VALUES.replace("DJANGO_NUM_PROXIES=2", "")
    env_file = f"DJANGO_SETTINGS_MODULE=config.settings.prod{values}"

    result = run_with_env_file(tmp_path, env_file, MANAGE)

    assert result.returncode != 0
    assert "DJANGO_NUM_PROXIES" in result.stderr


def test_prod_refuses_to_start_without_a_gemini_key(tmp_path):
    values = PROD_VALUES.replace("GEMINI_API_KEY=test-only", "")
    env_file = f"DJANGO_SETTINGS_MODULE=config.settings.prod{values}"

    result = run_with_env_file(tmp_path, env_file, MANAGE)

    assert result.returncode != 0
    assert "GEMINI_API_KEY" in result.stderr


def test_settings_flag_reaches_the_test_branch(tmp_path):
    env_file = (
        "DJANGO_SETTINGS_MODULE=config.settings.dev\n"
        "DATABASE_URL=postgres://u:p@ep-main/neondb\n"
        "TEST_DATABASE_URL=postgres://u:p@ep-test/neondb\n"
    )
    print_host = "from django.conf import settings; print(settings.DATABASES['default']['HOST'])"
    args = ["manage.py", "shell", "-v", "0", "--settings=config.settings.test", "-c", print_host]

    result = run_with_env_file(tmp_path, env_file, args)

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "ep-test"
