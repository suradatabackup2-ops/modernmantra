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

# Serve user-uploaded media in DEBUG mode (Django dev server only).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
