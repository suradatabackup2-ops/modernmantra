from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("newsletter/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("packages.json", views.packages_json, name="packages_json"),
]
