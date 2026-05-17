"""Catalog views — newsletter signup + JSON list of packages."""
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import NewsletterSubscriber, Package


@require_POST
def newsletter_subscribe(request):
    email = (request.POST.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return JsonResponse({"ok": False, "error": "Please enter a valid email."}, status=400)
    source = request.POST.get("source", "footer")
    obj, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={"source": source},
    )
    if not created and not obj.is_active:
        # Re-subscribe a previously unsubscribed user
        obj.is_active = True
        obj.unsubscribed_at = None
        obj.save(update_fields=["is_active", "unsubscribed_at"])
    return JsonResponse({"ok": True, "subscribed": True})


def packages_json(request):
    """JSON dump of active packages — handy for future SPA / mobile use."""
    qs = Package.objects.filter(is_active=True).order_by("display_order", "name")
    data = [
        {
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "category": p.category,
            "price": p.price,
            "price_label": p.price_label,
            "duration": p.duration_label,
            "short_description": p.short_description,
            "image_url": p.hero_image.url if p.hero_image else None,
            "brochure_url": p.brochure_pdf.url if p.brochure_pdf else None,
            "coming_soon": p.coming_soon,
            "is_featured": p.is_featured,
        }
        for p in qs
    ]
    return JsonResponse({"ok": True, "packages": data})
