"""Context processors for the pages app."""
from django.conf import settings


def site_globals(request):
    """Expose contact info and site-wide values to every template."""
    # Lazy imports — avoid app-loading issues at startup.
    from apps.bookings.models import Review
    from apps.catalog.models import Package

    approved_reviews = list(
        Review.objects.filter(approved=True).order_by("-created_at")[:8]
    )
    # Featured trips for the home page preview.
    # First try to find trips explicitly marked as featured. If none are
    # featured (common when an admin adds new packages and forgets to tick
    # the box), fall back to the first 3 active trips by display_order so
    # something useful always shows up on home.
    featured_packages = list(
        Package.objects.filter(is_active=True, is_featured=True).order_by("display_order")[:6]
    )
    if not featured_packages:
        featured_packages = list(
            Package.objects.filter(is_active=True).order_by("display_order")[:3]
        )

    return {
        "SITE_CONTACT": getattr(settings, "SITE_CONTACT", {}),
        "current_path": request.path,
        "approved_reviews": approved_reviews,
        "featured_packages": featured_packages,
    }
