"""Django forms — server-side validation for submissions."""
from django import forms

from .models import Booking, Enquiry, Registration, Review


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ["name", "phone", "email", "destination", "group_size", "month", "budget", "message"]


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["name", "phone", "email", "package", "price", "persons", "preferred_date"]


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["name", "city", "rating", "package", "body"]


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ["name", "phone", "email", "trip", "batch_date", "notes"]
