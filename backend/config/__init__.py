"""Loads .env before Django starts, so the file can set DJANGO_SETTINGS_MODULE."""

from pathlib import Path

import environ

environ.Env.read_env(Path(__file__).resolve().parent.parent / ".env")
