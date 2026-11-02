# Build from /backend. Run `migrate` before a new image goes live: see "Deploy to a host" in README.md.
FROM python:3.11-slim-bookworm

RUN pip install --no-cache-dir uv==0.13.6

WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev
COPY . .

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=config.settings.prod

# These only let prod settings load. collectstatic opens no database, and none reach the running app.
RUN DJANGO_SECRET_KEY=build DJANGO_ALLOWED_HOSTS=build DJANGO_NUM_PROXIES=0 \
    DATABASE_URL=postgres://build/build CORS_ALLOWED_ORIGINS=http://build \
    GEMINI_API_KEY=build RESEND_API_KEY=build \
    python manage.py collectstatic --noinput

RUN useradd --create-home app
USER app

# Exactly one process: the live socket's channels and the scheduler both live in its memory.
CMD ["sh", "-c", "exec daphne -b 0.0.0.0 -p ${PORT:-8000} config.asgi:application"]
