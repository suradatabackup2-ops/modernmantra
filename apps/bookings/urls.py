from django.urls import path

from . import views

app_name = "bookings"

urlpatterns = [
    path("enquiry/",      views.enquiry_create,      name="enquiry_create"),
    path("booking/",      views.booking_create,      name="booking_create"),
    path("review/",       views.review_create,       name="review_create"),
    path("registration/", views.registration_create, name="registration_create"),
]
