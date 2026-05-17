"""Public page views.

These pages are static — they render the templates directly.
The contact page has a separate form-handling endpoint in apps.bookings.
"""
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import DetailView, TemplateView


class HomeView(TemplateView):
    template_name = "pages/home.html"


class AboutView(TemplateView):
    template_name = "pages/about.html"


class PackagesView(TemplateView):
    template_name = "pages/packages.html"

    def get_context_data(self, **kwargs):
        import json
        from apps.catalog.models import Package
        ctx = super().get_context_data(**kwargs)
        today = timezone.now().date()

        # Build prices dict: { "Trip Name": price_int, ... }
        # Keyed by the package name so JS can match against data-trip / .pkg-name
        prices = {}
        batches = {}

        packages = Package.objects.filter(is_active=True).prefetch_related("batches")
        for pkg in packages:
            # Key = data_trip if set, else package name (must match data-trip HTML attr)
            key = pkg.data_trip.strip() if pkg.data_trip else pkg.name
            prices[key] = pkg.price
            upcoming = [
                b for b in pkg.batches.all()
                if b.start_date >= today and b.status != "closed"
            ]
            if upcoming:
                batches[key] = [
                    {
                        "id": b.id,
                        "startDate": b.start_date.isoformat(),
                        "endDate": b.end_date.isoformat(),
                        "label": b.start_date.strftime("%d %b") + " – " + b.end_date.strftime("%d %b %Y"),
                        "totalSpots": b.slots_total,
                        "filledSpots": b.slots_booked,
                        "status": b.status,
                    }
                    for b in upcoming[:6]
                ]

        ctx["db_prices_json"] = json.dumps(prices)
        ctx["db_batches_json"] = json.dumps(batches)

        # Flat list for the "Upcoming Departures" section — all future batches across all trips
        from apps.catalog.models import Batch
        upcoming_all = (
            Batch.objects
            .filter(start_date__gte=today, status__in=["open", "filling", "waitlist"])
            .select_related("package")
            .order_by("start_date")[:20]
        )
        ctx["upcoming_departures"] = upcoming_all
        return ctx


class GalleryView(TemplateView):
    template_name = "pages/gallery.html"


class ContactView(TemplateView):
    template_name = "pages/contact.html"


class PackageDetailView(DetailView):
    """Detail page for a single Package — shareable URL with full info."""
    template_name = "pages/package_detail.html"
    slug_url_kwarg = "slug"
    context_object_name = "package"

    def get_queryset(self):
        # Lazy import to avoid app-loading issues
        from apps.catalog.models import Package
        return Package.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        from apps.bookings.models import Review
        from apps.catalog.models import Package

        ctx = super().get_context_data(**kwargs)
        package = self.object
        today = timezone.now().date()

        # Upcoming batches for this package (those starting today or later)
        ctx["upcoming_batches"] = package.batches.filter(
            start_date__gte=today
        ).order_by("start_date")[:4]

        # Approved reviews mentioning this package
        ctx["package_reviews"] = Review.objects.filter(
            approved=True, package__icontains=package.name.split("–")[0].strip()[:30]
        ).order_by("-created_at")[:3]

        # Three other featured packages for the "you might also like" section
        ctx["related_packages"] = (
            Package.objects
            .filter(is_active=True)
            .exclude(id=package.id)
            .filter(is_featured=True)
            .order_by("display_order")[:3]
        )

        # Pre-filled WhatsApp message for the "Ask on WhatsApp" CTA
        ctx["wa_message"] = (
            f"Hi! I'm interested in the {package.name} trip "
            f"(₹{package.price:,} per person). Could you share more details?"
        )

        return ctx
