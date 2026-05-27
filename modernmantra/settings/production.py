"""
Production settings.

All secrets and host config come from environment variables. The Dockerfile
sets DJANGO_SETTINGS_MODULE=modernmantra.settings.production.

Required env vars:
    DJANGO_SECRET_KEY            — random 50+ char string
    DJANGO_ALLOWED_HOSTS         — comma-separated, e.g. "modernmantra.com,www.modernmantra.com"
    DJANGO_CSRF_TRUSTED_ORIGINS  — comma-separated, e.g. "https://modernmantra.com,https://www.modernmantra.com"

Optional:
    DATABASE_URL                 — postgres://USER:PASS@HOST:PORT/DB (omit to use SQLite at /app/db.sqlite3)
    EMAIL_*                      — see base.py
    SECURE_SSL_REDIRECT          — 1/0, default 1
"""
import os

# Make sure DEBUG is OFF before importing base.
os.environ.setdefault("DJANGO_DEBUG", "False")

from .base import *  # noqa: E402, F401, F403


# ─── Hard guard ──────────────────────────────────────────────────────
if SECRET_KEY.startswith("django-insecure-") or SECRET_KEY.startswith("dev-insecure-"):
    raise RuntimeError(
        "DJANGO_SECRET_KEY is unset or still the insecure default. "
        "Generate one: `python -c 'import secrets; print(secrets.token_urlsafe(64))'`"
    )

DEBUG = False


# ─── HTTPS / security ────────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
PREPEND_WWW = env_bool("PREPEND_WWW", False)