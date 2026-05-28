from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalog"
    label = "catalog"
    verbose_name = "Trip catalog"

    def ready(self):
        # Log the active media backend + a sample URL once at boot so the
        # config is verifiable straight from the platform logs.
        from modernmantra.storage import log_media_storage_diagnostics

        log_media_storage_diagnostics()
