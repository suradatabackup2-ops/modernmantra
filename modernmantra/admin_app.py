"""Admin app config — minimal branding only, standard Django admin UI."""
from django.contrib.admin.apps import AdminConfig
from django.contrib import admin


class ModernMantraAdminSite(admin.AdminSite):
    site_header = "Modern Mantra Admin"
    site_title  = "Modern Mantra Admin"
    index_title = "Dashboard"


class ModernMantraAdminConfig(AdminConfig):
    """Replaces 'django.contrib.admin' in INSTALLED_APPS."""
    default_site = "modernmantra.admin_app.ModernMantraAdminSite"
