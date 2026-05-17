"""Admin for the catalog app (Packages, Batches, Newsletter).

Three things to know:

1. Package admin keeps the full fieldset — Packages are content you
   manage carefully (descriptions, pricing, brochures), so we don't
   simplify it.

2. Batch admin's "Add Batch" form is minimal: pick a Package (only
   active ones), pick start + end dates, set slots. That's it.
   Everything else (slots_booked default 0, price_override blank,
   notes blank, status default 'open') gets sensible defaults and is
   only shown when editing an existing batch.

3. NewsletterSubscriber admin gains CSV export and bulk unsubscribe.
"""
import csv

from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Batch, NewsletterSubscriber, Package


# ─── Inline: Batches shown on the Package edit page ──────────────────
class BatchInline(admin.TabularInline):
    model = Batch
    extra = 1
    fields = ("start_date", "end_date", "slots_total", "status")
    show_change_link = True


# ─── Package admin ───────────────────────────────────────────────────
@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        "name", "category", "price_label", "duration_label",
        "is_active", "is_featured", "coming_soon", "has_brochure", "display_order",
    )
    list_filter = ("category", "is_active", "is_featured", "coming_soon")
    search_fields = ("name", "short_description", "long_description")
    list_editable = ("is_active", "is_featured", "coming_soon", "display_order")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [BatchInline]
    fieldsets = (
        (None, {
            "fields": ("name", "data_trip", "slug", "category",
                       "short_description", "long_description"),
        }),
        ("Pricing & duration", {
            "fields": ("price", "duration_days", "duration_nights"),
        }),
        ("Media", {
            "fields": ("hero_image", "brochure_pdf"),
        }),
        ("Display flags", {
            "fields": ("is_active", "is_featured", "coming_soon", "display_order"),
        }),
    )

    def has_brochure(self, obj):
        if obj.brochure_pdf:
            return format_html(
                '<a href="{}" target="_blank">📄 View</a>',
                obj.brochure_pdf.url,
            )
        return "—"
    has_brochure.short_description = "Brochure"


# ─── Batch admin (the "Upcoming Batches" page from the old admin) ────
class BatchAdminForm(forms.ModelForm):
    """Force the Package dropdown to only show active packages, ordered nicely."""

    class Meta:
        model = Batch
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit the Package dropdown to active packages, ordered by display_order
        if "package" in self.fields:
            self.fields["package"].queryset = (
                Package.objects.filter(is_active=True).order_by("display_order", "name")
            )
            self.fields["package"].empty_label = "— Select a trip —"


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    form = BatchAdminForm

    list_display = (
        "package", "start_date", "end_date", "status_badge",
        "slots_total", "slots_booked", "display_slots_left",
    )
    list_filter = ("status", "package")
    search_fields = ("package__name", "notes")
    date_hierarchy = "start_date"

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return format_html(
            '<span class="mm-badge mm-badge-{}">{}</span>',
            obj.status, obj.get_status_display(),
        )

    @admin.display(description="Slots left", ordering="slots_total")
    def display_slots_left(self, obj):
        left = obj.slots_left
        color = "#2e7d32" if left > 8 else "#e65100" if left > 0 else "#c62828"
        return format_html('<strong style="color:{}">{}</strong>', color, left)

    def get_fieldsets(self, request, obj=None):
        """Minimal form on add; full form on edit."""
        if obj is None:
            # Add Batch — the only four things you actually need to enter
            return (
                ("New batch", {
                    "fields": ("package", "start_date", "end_date", "slots_total"),
                    "description": (
                        "Pick a trip from your active packages and the departure dates. "
                        "Status defaults to 'Open' — change it later when the batch fills up."
                    ),
                }),
            )
        # Editing — show everything
        return (
            ("Trip", {
                "fields": ("package",),
            }),
            ("Dates", {
                "fields": ("start_date", "end_date"),
            }),
            ("Capacity", {
                "fields": ("slots_total", "slots_booked", "status"),
            }),
            ("Optional", {
                "fields": ("price_override", "notes"),
                "classes": ("collapse",),
            }),
        )


# ─── Newsletter admin ────────────────────────────────────────────────
@admin.register(NewsletterSubscriber)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "subscribed_at", "source")
    list_filter = ("is_active", "subscribed_at", "source")
    search_fields = ("email",)
    readonly_fields = ("subscribed_at", "unsubscribed_at")
    list_editable = ("is_active",)
    actions = ["export_csv", "mark_unsubscribed"]

    def export_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="newsletter.csv"'
        writer = csv.writer(response)
        writer.writerow(["email", "subscribed_at", "is_active", "source"])
        for s in queryset:
            writer.writerow([s.email, s.subscribed_at.isoformat(), s.is_active, s.source])
        return response
    export_csv.short_description = "Export selected to CSV"

    def mark_unsubscribed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(is_active=False, unsubscribed_at=timezone.now())
        messages.success(request, f"{updated} subscriber(s) unsubscribed.")
    mark_unsubscribed.short_description = "Mark as unsubscribed"
