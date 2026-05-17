"""
Media storage configuration for uploaded files (PDFs, package images).

The MEDIA_STORAGE_BACKEND env var picks the backend:

    local  (default)  → filesystem at MEDIA_ROOT — fine for dev,
                        works on Lightsail VMs with persistent disk
    r2                → Cloudflare R2 (S3-compatible, NO egress fees)
    s3                → AWS S3
    b2                → Backblaze B2 (S3-compatible, cheapest cold storage)
    do                → DigitalOcean Spaces (S3-compatible)

Each cloud backend needs these env vars:

    MEDIA_BUCKET_NAME              the bucket / Space name
    MEDIA_ACCESS_KEY_ID            access key
    MEDIA_SECRET_ACCESS_KEY        secret key
    MEDIA_CUSTOM_DOMAIN            optional — your CDN domain
                                   (e.g. "cdn.modernmantra.com")
    MEDIA_REGION                   region — see backend specifics below

Backend-specific URLs:

    R2:   endpoint = https://<account_id>.r2.cloudflarestorage.com
          → set MEDIA_ENDPOINT_URL to that, MEDIA_REGION="auto"
    S3:   endpoint inferred from region (MEDIA_REGION="ap-south-1" for Mumbai)
    B2:   endpoint = https://s3.<region>.backblazeb2.com
          → set MEDIA_ENDPOINT_URL, MEDIA_REGION e.g. "us-west-002"
    DO:   endpoint = https://<region>.digitaloceanspaces.com
          → set MEDIA_ENDPOINT_URL, MEDIA_REGION e.g. "blr1"
"""
import os
from pathlib import Path


def configure_media_storage(storages: dict, base_dir: Path) -> dict:
    """Mutate-and-return the STORAGES dict based on MEDIA_STORAGE_BACKEND."""
    backend = os.environ.get("MEDIA_STORAGE_BACKEND", "local").lower()

    if backend == "local":
        # Default — files live under MEDIA_ROOT on the container's filesystem.
        # On stateless platforms (App Runner, Fargate) this means files are
        # lost on every redeploy — use a real object store for production.
        storages["default"] = {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
            "OPTIONS": {
                "location": str(base_dir / "media"),
                "base_url": "/media/",
            },
        }
        return storages

    # All cloud backends use the same django-storages S3Storage class —
    # they just differ in endpoint URL, region, and custom domain.
    options = {
        "bucket_name": os.environ["MEDIA_BUCKET_NAME"],
        "access_key": os.environ["MEDIA_ACCESS_KEY_ID"],
        "secret_key": os.environ["MEDIA_SECRET_ACCESS_KEY"],
        "region_name": os.environ.get("MEDIA_REGION", "auto"),
        "querystring_auth": False,
        "file_overwrite": False,
        "object_parameters": {
            "CacheControl": "public, max-age=31536000, immutable",
        },
    }

    endpoint = os.environ.get("MEDIA_ENDPOINT_URL", "")
    if endpoint:
        options["endpoint_url"] = endpoint

    custom_domain = os.environ.get("MEDIA_CUSTOM_DOMAIN", "")
    if custom_domain:
        options["custom_domain"] = custom_domain

    # Backend-specific defaults
    if backend == "r2":
        # Cloudflare R2: no egress fees, S3-compatible.
        options.setdefault("region_name", "auto")
        # R2 requires signature_version="s3v4"
        options["signature_version"] = "s3v4"

    storages["default"] = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": options,
    }
    return storages
