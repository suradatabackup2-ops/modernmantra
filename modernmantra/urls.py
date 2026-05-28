from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from .sitemaps import sitemaps_dict

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(("apps.bookings.urls", "bookings"), namespace="bookings")),
    path("api/catalog/", include(("apps.catalog.urls", "catalog"), namespace="catalog")),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps_dict},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("", include(("apps.pages.urls", "pages"), namespace="pages")),
]

# Serve uploaded media files via Django when using local filesystem storage.
# In development (DEBUG=True) this was already active.
# In production with MEDIA_STORAGE_BACKEND=local (the default), the /media/
# route was missing — causing hero images to 404 on every page.
# Cloud backends (R2/S3/B2/DO) serve files from their own CDN so this route
# is harmless but unused when those backends are configured.
import os as _os
_local_storage = _os.environ.get("MEDIA_STORAGE_BACKEND", "local").lower() == "local"
if settings.DEBUG or _local_storage:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
