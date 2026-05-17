"""Django admin for submissions (Enquiry, Booking, Review, Registration).

Key design choices:

1. Booking.package is a CharField (free text). The public website form
   posts whatever the customer typed. In the admin's "Add Booking" form
   we render a dropdown sourced from the active Package catalog so the
   team picks a canonical name instead of retyping it.

2. The add-form (used when an admin manually creates a row) shows only
   the essentials. The change-form (used when editing an existing row)
   shows everything, so all data — including status and admin_notes —
   remains editable.

3. The list view always shows everything plus inline status editing,
   bulk status actions, and CSV export.
"""
import csv
from typing import Iterable

from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse
from django.utils.html import format_html

from .models import Booking, Enquiry, Registration, Review, Status


# ─── Helper: render a color-coded status badge ───────────────────────
def _status_badge(value, display=None):
    if not value:
        return "—"
    label = display or value
    return format_html(
        '<span class="mm-badge mm-badge-{}">{}</span>',
        value, label,
    )


# ─── Bulk action: export to CSV ──────────────────────────────────────
def _export_csv(modeladmin, request, queryset, fields: Iterable[str], filename: str):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(fields)
    for obj in queryset:
        writer.writerow([getattr(obj, f, "") for f in fields])
    return response


# ─── Status bulk actions ─────────────────────────────────────────────
def _bulk_set_status(status_value: str, label: str):
    def action(modeladmin, request, queryset):
        updated = queryset.update(status=status_value)
        messages.success(request, f"{updated} item(s) marked as {label}.")

    action.short_description = f"Mark selected as {label}"
    action.__name__ = f"set_status_{status_value}"
    return action


# ─── Enquiry admin ───────────────────────────────────────────────────
@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "name", "phone", "email", "destination",
        "group_size", "month", "budget", "status_badge", "created_at",
    )
    list_filter = ("status", "destination", "month", "budget", "created_at")
    search_fields = ("name", "phone", "email", "destination", "message")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 50
    date_hierarchy = "created_at"

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return _status_badge(obj.status, obj.get_status_display())

    actions = [
        _bulk_set_status(Status.CONTACTED, "Contacted"),
        _bulk_set_status(Status.CONFIRMED, "Confirmed"),
        _bulk_set_status(Status.CANCELLED, "Cancelled"),
        _bulk_set_status(Status.SPAM, "Spam"),
        "export_csv",
    ]

    def get_fieldsets(self, request, obj=None):
        """Simpler form on add; full form on edit."""
        if obj is None:
            # Add form — show only what a human typing it would care about
            return (
                ("Contact", {
                    "fields": ("name", "phone", "email"),
                }),
                ("Trip details", {
                    "fields": ("destination", "group_size", "month", "budget", "message"),
                }),
            )
        # Edit form — full set
        return (
            ("Contact", {
                "fields": ("name", "phone", "email"),
            }),
            ("Trip details", {
                "fields": ("destination", "group_size", "month", "budget", "message"),
            }),
            ("Workflow", {
                "fields": ("status", "admin_notes"),
            }),
            ("Audit", {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            }),
        )

    def export_csv(self, request, queryset):
        return _export_csv(
            self, request, queryset,
            fields=["created_at", "name", "phone", "email", "destination",
                    "group_size", "month", "budget", "message", "status"],
            filename="enquiries.csv",
        )
    export_csv.short_description = "Export selected to CSV"


# ─── Booking admin ───────────────────────────────────────────────────
class BookingAdminForm(forms.ModelForm):
    """Admin form that renders 'package' as a dropdown of active Package names.

    The underlying field is still a CharField, so anything the public
    website posts (free text from customer) keeps working. The dropdown
    just provides clean canonical values when staff create a booking by hand.
    """

    package = forms.ChoiceField(
        choices=[],
        label="Package",
        help_text="Choose a package from your catalog.",
    )

    class Meta:
        model = Booking
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Lazy import — avoid circular import at module load time
        from apps.catalog.models import Package as PackageModel

        active_names = list(
            PackageModel.objects
            .filter(is_active=True)
            .order_by("display_order", "name")
            .values_list("name", flat=True)
        )

        # Build choices. If the booking already has a package value that
        # isn't in the active list (e.g. from a customer who typed it on
        # the public site), include it so the form still works for edits.
        choices = [("", "— Select a package —")]
        current = self.initial.get("package") or getattr(self.instance, "package", "")
        seen = set()
        for name in active_names:
            choices.append((name, name))
            seen.add(name)
        if current and current not in seen:
            choices.append((current, f"{current} (custom)"))

        self.fields["package"].choices = choices

        # If the team hasn't added any active packages yet, fall back to a
        # plain text input so the admin form is still usable.
        if not active_names:
            self.fields["package"] = forms.CharField(
                label="Package",
                help_text="(No active packages yet — type a name.)",
            )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm

    list_display = (
        "name", "phone", "email", "package",
        "price", "persons", "preferred_date", "status_badge", "created_at",
    )
    list_filter = ("status", "package", "created_at")
    search_fields = ("name", "phone", "email", "package")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 50
    date_hierarchy = "created_at"

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return _status_badge(obj.status, obj.get_status_display())

    actions = [
        _bulk_set_status(Status.CONTACTED, "Contacted"),
        _bulk_set_status(Status.CONFIRMED, "Confirmed"),
        _bulk_set_status(Status.CANCELLED, "Cancelled"),
        "export_csv",
    ]

    def get_fieldsets(self, request, obj=None):
        """Simpler form on add; full form on edit."""
        if obj is None:
            return (
                ("Customer", {
                    "fields": ("name", "phone", "email"),
                }),
                ("Booking", {
                    "fields": ("package", "persons", "preferred_date"),
                    "description": "Status defaults to 'New'. Price auto-fills from the selected package.",
                }),
            )
        return (
            ("Customer", {
                "fields": ("name", "phone", "email"),
            }),
            ("Booking", {
                "fields": ("package", "price", "persons", "preferred_date"),
            }),
            ("Workflow", {
                "fields": ("status", "admin_notes"),
            }),
            ("Audit", {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            }),
        )

    def save_model(self, request, obj, form, change):
        """When adding a booking and price wasn't entered, copy it from the chosen Package."""
        if not obj.price and obj.package:
            from apps.catalog.models import Package as PackageModel
            match = PackageModel.objects.filter(name=obj.package, is_active=True).first()
            if match and match.price:
                obj.price = f"₹{match.price:,}"
        super().save_model(request, obj, form, change)

    def export_csv(self, request, queryset):
        return _export_csv(
            self, request, queryset,
            fields=["created_at", "name", "phone", "email", "package",
                    "price", "persons", "preferred_date", "status"],
            filename="bookings.csv",
        )
    export_csv.short_description = "Export selected to CSV"


# ─── Review admin ────────────────────────────────────────────────────
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "rating_stars", "city", "package", "approved_badge", "created_at")
    list_filter = ("approved", "rating", "created_at")
    search_fields = ("name", "city", "package", "body")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 50

    def rating_stars(self, obj):
        return format_html("<span style='color:#d4a017;font-size:1.05rem'>{}</span>", "★" * obj.rating)
    rating_stars.short_description = "Rating"
    rating_stars.admin_order_field = "rating"

    @admin.display(description="Status", ordering="approved")
    def approved_badge(self, obj):
        if obj.approved:
            return format_html('<span class="mm-badge mm-badge-approved">Approved</span>')
        return format_html('<span class="mm-badge mm-badge-pending">Pending</span>')

    actions = ["approve_selected", "unapprove_selected"]

    def approve_selected(self, request, queryset):
        updated = queryset.update(approved=True)
        messages.success(request, f"{updated} review(s) approved.")
    approve_selected.short_description = "Approve selected reviews"

    def unapprove_selected(self, request, queryset):
        updated = queryset.update(approved=False)
        messages.success(request, f"{updated} review(s) unapproved.")
    unapprove_selected.short_description = "Unapprove selected reviews"


# ─── Registration admin ──────────────────────────────────────────────
@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "trip", "batch_date", "status_badge", "created_at")
    list_filter = ("status", "trip", "created_at")
    search_fields = ("name", "phone", "email", "trip")
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        return _status_badge(obj.status, obj.get_status_display())


admin.site.site_header = "Modern Mantra — Admin"
admin.site.site_title = "Modern Mantra Admin"
admin.site.index_title = "Submissions & content"
