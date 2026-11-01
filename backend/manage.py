#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys


def main():
    """Run administrative tasks."""
    try:
        from django.core.management import execute_from_command_line

        # Importing config loads .env, which names the settings module.
        import config  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # Migrations need a direct connection; the app stays on the pooled DATABASE_URL.
    if "migrate" in sys.argv and os.environ.get("DIRECT_URL"):
        os.environ["DATABASE_URL"] = os.environ["DIRECT_URL"]
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
