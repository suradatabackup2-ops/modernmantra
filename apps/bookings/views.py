"""Form-submission endpoints.

The original JS posted to Formspree + Google Apps Script. We replace both
with Django endpoints that save to the database and (optionally) email
the admins.

All endpoints accept POST with either form-encoded or JSON body, return
{"ok": true, "id": <pk>} on success, or {"ok": false, "errors": {...}}.
"""
from __future__ import annotations

import json
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_POST

from .forms import BookingForm, EnquiryForm, RegistrationForm, ReviewForm
from .webhooks import mirror_booking, mirror_enquiry, mirror_review

logger = logging.getLogger(__name__)


# ─── Helpers ─────────────────────────────────────────────────────────
# The original JS forms use TitleCase field names (Name, Phone, Email,
# GroupSize, Message, etc.). We map them to our snake_case ModelForm fields.
FIELD_MAP = {
    "Name": "name",
    "Phone": "phone",
    "Email": "email",
    "Destination": "destination",
    "GroupSize": "group_size",
    "Group_Size": "group_size",
    "Month": "month",
    "Budget": "budget",
    "Message": "message",
    "Package": "package",
    "Price": "price",
    "Persons": "persons",
    "Date": "preferred_date",
    "PreferredDate": "preferred_date",
    "City": "city",
    "Rating": "rating",
    "Body": "body",
    "Review": "body",
    "Trip": "trip",
    "BatchDate": "batch_date",
    "Notes": "notes",
}


def _normalize_payload(request) -> dict:
    """Return a flat dict with Django field names, accepting JSON or form-encoded."""
    raw: dict = {}
    ctype = (request.content_type or "").lower()
    if "application/json" in ctype:
        try:
            raw = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            raw = {}
    else:
        raw = dict(request.POST.items())

    out: dict = {}
    for k, v in raw.items():
        target = FIELD_MAP.get(k, k)
        # Don't overwrite an already-correct snake_case key
        if target not in out or out[target] in ("", None):
            out[target] = v
    return out


def _notify_admins(subject: str, body: str) -> None:
    recipients = settings.NOTIFY_EMAILS
    if not recipients:
        return
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=True,
        )
    except Exception as exc:  # email failures should not break submissions
        logger.warning("Admin notification failed: %s", exc)


def _bad_request(form) -> JsonResponse:
    return JsonResponse({"ok": False, "errors": form.errors}, status=400)


# ─── Endpoints ───────────────────────────────────────────────────────
@require_POST
def enquiry_create(request):
    data = _normalize_payload(request)
    form = EnquiryForm(data)
    if not form.is_valid():
        return _bad_request(form)
    obj = form.save()
    _notify_admins(
        subject=f"📩 New enquiry from {obj.name}",
        body=(
            f"Name: {obj.name}\nPhone: {obj.phone}\nEmail: {obj.email}\n"
            f"Destination: {obj.destination or '—'}\nGroup: {obj.group_size or '—'}\n"
            f"Month: {obj.month or '—'}\nBudget: {obj.budget or '—'}\n"
            f"Message: {obj.message or '—'}\n"
        ),
    )
    mirror_enquiry(obj)
    return JsonResponse({"ok": True, "id": obj.id})


@require_POST
def booking_create(request):
    data = _normalize_payload(request)
    form = BookingForm(data)
    if not form.is_valid():
        return _bad_request(form)
    obj = form.save()
    _notify_admins(
        subject=f"📋 New booking: {obj.name} → {obj.package}",
        body=(
            f"Customer: {obj.name}\nPhone: {obj.phone}\nEmail: {obj.email}\n"
            f"Package: {obj.package}\nPrice: {obj.price or '—'}\n"
            f"Persons: {obj.persons or '—'}\nPreferred date: {obj.preferred_date or '—'}\n"
        ),
    )
    mirror_booking(obj)
    return JsonResponse({"ok": True, "id": obj.id})


@require_POST
def review_create(request):
    data = _normalize_payload(request)
    # Default rating to 5 if not provided
    if "rating" not in data or not str(data.get("rating", "")).strip():
        data["rating"] = 5
    form = ReviewForm(data)
    if not form.is_valid():
        return _bad_request(form)
    obj = form.save()
    _notify_admins(
        subject=f"⭐ New review ({obj.rating}★) from {obj.name}",
        body=(
            f"Name: {obj.name}\nCity: {obj.city or '—'}\nRating: {obj.rating}\n"
            f"Package: {obj.package or '—'}\n\n{obj.body}\n\n"
            f"Approve in admin to publish on the site.\n"
        ),
    )
    mirror_review(obj)
    return JsonResponse({"ok": True, "id": obj.id})


@require_POST
def registration_create(request):
    data = _normalize_payload(request)
    form = RegistrationForm(data)
    if not form.is_valid():
        return _bad_request(form)
    obj = form.save()
    _notify_admins(
        subject=f"🙌 New registration: {obj.name}",
        body=(
            f"Name: {obj.name}\nPhone: {obj.phone}\nEmail: {obj.email}\n"
            f"Trip: {obj.trip or '—'}\nBatch: {obj.batch_date or '—'}\n"
            f"Notes: {obj.notes or '—'}\n"
        ),
    )
    return JsonResponse({"ok": True, "id": obj.id})
