"""
ensure_superuser — non-interactive superuser provisioning for production.

Reads credentials from environment variables and creates an admin user if
none exists yet. Designed to be safe to run on every deploy:

  • If the user already exists  → does nothing (no errors, no overwrites).
  • If credentials are missing  → logs a friendly warning and exits 0.
  • If creation fails           → logs the error and exits 0 (never breaks deploys).

Trigger from the Dockerfile entrypoint or any post-deploy hook:

    python manage.py ensure_superuser

Required env vars (all three must be set for creation to actually happen):
    DJANGO_SUPERUSER_USERNAME    e.g. "admin"
    DJANGO_SUPERUSER_EMAIL       e.g. "you@example.com"
    DJANGO_SUPERUSER_PASSWORD    a strong password, NEVER commit this

Optional:
    DJANGO_SUPERUSER_RESET=1     if set, will RESET the password of an
                                 existing user with the same username to
                                 match DJANGO_SUPERUSER_PASSWORD (handy if
                                 you forgot your admin password — set this,
                                 redeploy, then unset it and redeploy again).
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or refresh a Django superuser from environment variables (non-interactive)."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        email    = os.environ.get("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")

        if not username or not email or not password:
            self.stdout.write(self.style.WARNING(
                "ensure_superuser: Missing one or more of "
                "DJANGO_SUPERUSER_{USERNAME,EMAIL,PASSWORD} — skipping."
            ))
            return

        User = get_user_model()

        try:
            existing = User.objects.filter(username=username).first()

            if existing is None:
                User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                )
                self.stdout.write(self.style.SUCCESS(
                    f"ensure_superuser: Created superuser '{username}'."
                ))
                return

            # User exists. By default, don't touch it — admins may have
            # rotated the password manually from the UI and we don't want
            # to clobber it on every deploy.
            if not os.environ.get("DJANGO_SUPERUSER_RESET"):
                self.stdout.write(self.style.NOTICE(
                    f"ensure_superuser: User '{username}' already exists "
                    "— leaving as is. (Set DJANGO_SUPERUSER_RESET=1 to "
                    "reset password to env value.)"
                ))
                return

            # Explicit reset requested. Update password + ensure flags.
            existing.email = email
            existing.set_password(password)
            existing.is_staff = True
            existing.is_superuser = True
            existing.is_active = True
            existing.save()
            self.stdout.write(self.style.SUCCESS(
                f"ensure_superuser: Reset password for '{username}'."
            ))

        except Exception as exc:
            # Never break the deploy. Log and move on.
            self.stdout.write(self.style.ERROR(
                f"ensure_superuser: Skipping due to error: {exc!r}"
            ))
