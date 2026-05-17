"""WSGI config for the Modern Mantra project."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "modernmantra.settings.production")

application = get_wsgi_application()
