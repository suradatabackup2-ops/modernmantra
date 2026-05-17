# syntax=docker/dockerfile:1.7

# ───────────────────────── Builder stage ─────────────────────────────
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build deps for any C extensions (psycopg, Pillow, etc.).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .

# Install into a separate prefix so we can copy only what we need to the
# runtime image. Smaller final image, fewer attack surface bytes.
RUN pip install --prefix=/install -r requirements.txt


# ───────────────────────── Runtime stage ─────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=modernmantra.settings.production \
    PORT=8000 \
    PATH="/usr/local/bin:$PATH"

# Runtime-only system libs (libpq for psycopg, curl for healthchecks).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security.
RUN groupadd --system app && useradd --system --gid app --home /app app

WORKDIR /app

# Copy installed Python packages from builder.
COPY --from=builder /install /usr/local

# Copy application code.
COPY --chown=app:app . .

# Collect static files at build time (fingerprinted, gzipped/brotli'd by WhiteNoise).
# DJANGO_SECRET_KEY is required by base settings — we pass a throwaway one
# just for collectstatic. The real secret comes from the runtime env.
RUN DJANGO_SECRET_KEY="build-only-not-used-at-runtime-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
    DJANGO_ALLOWED_HOSTS="*" \
    SECURE_SSL_REDIRECT="0" \
    python manage.py collectstatic --noinput

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -fsS http://localhost:${PORT}/ || exit 1

# Migrate-on-start is convenient for single-instance deployments
# (Lightsail, Render, Fly free tier). For multi-instance fleets (ECS,
# multi-replica Beanstalk), run migrations in a separate one-off task
# and remove the migrate step from here.
#
# seed_packages is idempotent — running it on every container start
# only inserts trips that don't already exist. To force-refresh existing
# rows with new prices/descriptions, run `python manage.py seed_packages
# --update` once manually from the Railway terminal.
CMD sh -c "python manage.py migrate --noinput && \
           python manage.py seed_packages && \
           exec gunicorn modernmantra.wsgi:application \
                --bind 0.0.0.0:${PORT} \
                --workers ${WEB_CONCURRENCY:-3} \
                --threads ${WEB_THREADS:-2} \
                --timeout 60 \
                --access-logfile - \
                --error-logfile -"
