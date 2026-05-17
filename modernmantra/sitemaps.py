"""Sitemap definitions."""
from django.contrib import sitemaps
from django.urls import reverse


class StaticPagesSitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ["home", "about", "packages", "gallery", "contact"]

    def location(self, item):
        return reverse(f"pages:{item}")


class PackageSitemap(sitemaps.Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        from apps.catalog.models import Package
        return Package.objects.filter(is_active=True)

    def location(self, obj):
        return reverse("pages:package_detail", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


sitemaps_dict = {
    "static": StaticPagesSitemap,
    "packages": PackageSitemap,
}
