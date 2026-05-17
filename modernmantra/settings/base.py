"""
Shared Django settings for the Modern Mantra project.

Environment-specific overrides live in dev.py and production.py.
Reads secrets from environment variables (.env in dev, real env in prod).
"""
import os
from pathlib import Path

import dj_database_url


# ─── Paths ───────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # project root


# ─── Helpers ─────────────────────────────────────────────────────────
def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "on")


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# ─── Core ────────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-CHANGE-ME-in-production",
)
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")


# ─── Applications ────────────────────────────────────────────────────
INSTALLED_APPS = [
    "modernmantra.admin_app.ModernMantraAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    # Local apps
    "apps.pages",
    "apps.bookings",
    "apps.catalog",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # WhiteNoise serves static files efficiently in production.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "modernmantra.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.pages.context_processors.site_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "modernmantra.wsgi.application"


# ─── Database ────────────────────────────────────────────────────────
# Default: SQLite (file at <project>/db.sqlite3).
# Set DATABASE_URL=postgres://USER:PASS@HOST:PORT/DBNAME to switch to Postgres.
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# ─── Auth ────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ─── i18n ────────────────────────────────────────────────────────────
LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# ─── Static & media ──────────────────────────────────────────────────
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise: hashed filenames + gzip/brotli for production cache headers
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# ─── Default primary key ─────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ─── Pluggable media storage (local / R2 / S3 / B2 / DO Spaces) ──────
# See modernmantra/storage.py for the full list of env vars.
from modernmantra.storage import configure_media_storage  # noqa: E402

STORAGES = configure_media_storage(STORAGES, BASE_DIR)


# ─── Email ───────────────────────────────────────────────────────────
# Default: console backend (prints emails to stdout — good for dev).
# In production set EMAIL_BACKEND env var to:
#   django.core.mail.backends.smtp.EmailBackend  (for SMTP / Mailgun / SendGrid)
# and provide EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD,
# EMAIL_USE_TLS.
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "Modern Mantra <noreply@modernmantra.example>")
# Comma-separated list of admins to notify on new enquiries/bookings/reviews.
NOTIFY_EMAILS = env_list("NOTIFY_EMAILS", "ziyaziu17@gmail.com")


# ─── Site contact details ────────────────────────────────────────────
# Surfaced in templates via the site_globals context processor so the
# footer and contact page can stay in sync without editing HTML.
SITE_CONTACT = {
    "phone_primary": "+91 77368 55515",
    "phone_secondary": "+91 62380 53483",
    "email": "ziyaziu17@gmail.com",
    "whatsapp": "917736855515",
    "instagram": "modernmantra_",
}


# ─── Logging ─────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.environ.get("LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
