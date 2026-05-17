"""Development settings — DEBUG on, permissive hosts, console email."""
import os

os.environ.setdefault("DJANGO_DEBUG", "True")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", "*")

from .base import *  # noqa: E402, F401, F403

# Force these for safety in dev — even if .env overrides.
DEBUG = True
ALLOWED_HOSTS = ["*"]
SECRET_KEY = "dev-insecure-not-for-production-xK29sLp3qWnE4tYjR8bvF7dCm5gHnUaZ"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
