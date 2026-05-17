"""Catalog models — managed through the Django admin.

Adding a row in /admin/catalog/package/ uploads the brochure PDF to whichever
storage backend MEDIA_STORAGE_BACKEND points at (local / R2 / S3 / B2 / DO).
No code change needed when you switch backends.
"""
from django.db import models
from django.utils.text import slugify


class Category(models.TextChoices):
    HIMALAYAN_TREK = "trek", "Himalayan Trek"
    ROAD_TRIP = "road", "Road Trip"
    WEEKEND = "weekend", "Weekend Getaway"
    INTERNATIONAL = "intl", "International"
    BACKPACKING = "backpack", "Backpacking"
    LUXURY = "luxury", "Luxury"


def package_image_path(instance, filename):
    return f"packages/{instance.slug or 'pkg'}/hero/{filename}"


def package_brochure_path(instance, filename):
    return f"packages/{instance.slug or 'pkg'}/brochures/{filename}"


class Package(models.Model):
    """A travel package / trip offering.

    The brochure_pdf field uses Django's default storage, so it goes to
    whichever backend MEDIA_STORAGE_BACKEND specifies — including R2/S3
    when configured.
    """
    name = models.CharField(max_length=120, help_text="e.g. 'Spiti Valley 6D/5N'")
    slug = models.SlugField(max_length=140, unique=True, blank=True,
                            help_text="Auto-generated if left blank")
    category = models.CharField(max_length=16, choices=Category.choices, default=Category.HIMALAYAN_TREK)
    short_description = models.CharField(max_length=240, blank=True,
                                          help_text="One-line teaser shown on cards")
    long_description = models.TextField(blank=True,
                                         help_text="Full description for the detail page")

    # HTML card identifier — must match the data-trip attribute on the packages page card
    data_trip = models.CharField(
        max_length=200, blank=True,
        help_text="Must match the data-trip attribute on the packages.html card exactly. "
                  "Leave blank to auto-use the package name."
    )

    # Pricing
    price = models.PositiveIntegerField(help_text="Base price in INR")
    duration_days = models.PositiveSmallIntegerField(default=0)
    duration_nights = models.PositiveSmallIntegerField(default=0)

    # Display
    hero_image = models.ImageField(upload_to=package_image_path, blank=True)
    brochure_pdf = models.FileField(upload_to=package_brochure_path, blank=True,
                                     help_text="Itinerary PDF — uploads to your "
                                               "configured storage backend (R2 / S3 / etc).")

    # Flags
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Show in 'Featured' on home")
    coming_soon = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=100,
                                                       help_text="Lower numbers shown first")

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["display_order", "name"]
        indexes = [
            models.Index(fields=["is_active", "is_featured"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:140]
        super().save(*args, **kwargs)

    @property
    def duration_label(self) -> str:
        if self.duration_days and self.duration_nights:
            return f"{self.duration_days}D / {self.duration_nights}N"
        if self.duration_days:
            return f"{self.duration_days} days"
        return ""

    @property
    def price_label(self) -> str:
        return f"₹{self.price:,}" if self.price else ""


class Batch(models.Model):
    """A scheduled departure for a Package — what the old admin called 'batches'."""
    package = models.ForeignKey(Package, related_name="batches", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    slots_total = models.PositiveSmallIntegerField(default=20)
    slots_booked = models.PositiveSmallIntegerField(default=0)
    price_override = models.PositiveIntegerField(blank=True, null=True,
                                                   help_text="If set, overrides Package.price for this batch")
    notes = models.CharField(max_length=240, blank=True)

    STATUS_CHOICES = [
        ("open", "Open"),
        ("filling", "Filling fast"),
        ("waitlist", "Waitlist only"),
        ("closed", "Closed"),
    ]
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="open")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_date"]

    def __str__(self) -> str:
        return f"{self.package.name} — {self.start_date}"

    @property
    def slots_left(self) -> int:
        return max(0, self.slots_total - self.slots_booked)


class NewsletterSubscriber(models.Model):
    """Email signups from the footer / homepage."""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    source = models.CharField(max_length=64, blank=True, help_text="Which page/section")

    class Meta:
        ordering = ["-subscribed_at"]

    def __str__(self) -> str:
        return self.email
