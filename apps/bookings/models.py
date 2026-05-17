"""Data models that replace the old Google Sheets + localStorage backend.

Field shapes mirror what the existing JS posts in saveEnquiryLocal()
and saveBookingLocal() in js/main.js, plus the contact-page review form.
"""
from django.db import models


class Status(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    CONFIRMED = "confirmed", "Confirmed"
    CANCELLED = "cancelled", "Cancelled"
    SPAM = "spam", "Spam"


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


# ─── Enquiry ─────────────────────────────────────────────────────────
class Enquiry(TimestampedModel):
    """Form on contact.html — general enquiry / custom trip planning."""
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField()
    destination = models.CharField(max_length=120, blank=True)
    group_size = models.CharField(max_length=32, blank=True)
    month = models.CharField(max_length=32, blank=True)
    budget = models.CharField(max_length=32, blank=True)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    admin_notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Enquiries"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Enquiry from {self.name} ({self.destination or 'general'})"


# ─── Booking ─────────────────────────────────────────────────────────
class Booking(TimestampedModel):
    """Trip booking form (from packages.html)."""
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField()
    package = models.CharField(max_length=120)
    price = models.CharField(max_length=32, blank=True)
    persons = models.CharField(max_length=16, blank=True)
    preferred_date = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Booking: {self.name} → {self.package}"


# ─── Review ──────────────────────────────────────────────────────────
class Review(TimestampedModel):
    """Customer review form (modal on contact.html)."""
    RATING_CHOICES = [(i, "★" * i) for i in range(1, 6)]

    name = models.CharField(max_length=120)
    city = models.CharField(max_length=80, blank=True)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    package = models.CharField(max_length=120, blank=True)
    body = models.TextField()
    approved = models.BooleanField(default=False, help_text="Show on public site")
    admin_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.rating}★ — {self.name}"


# ─── Registration ────────────────────────────────────────────────────
class Registration(TimestampedModel):
    """Group-trip / batch registrations."""
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField()
    trip = models.CharField(max_length=120, blank=True)
    batch_date = models.CharField(max_length=64, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Registration: {self.name} → {self.trip or '(no trip)'}"
