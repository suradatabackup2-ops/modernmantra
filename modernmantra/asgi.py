"""ASGI config for the Modern Mantra project."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "modernmantra.settings.production")

application = get_asgi_application()
