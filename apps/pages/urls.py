from django.urls import path

from . import views

# Namespace is set in modernmantra/urls.py via include(..., namespace="pages")
app_name = "pages"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("packages/", views.PackagesView.as_view(), name="packages"),
    path("packages/<slug:slug>/", views.PackageDetailView.as_view(), name="package_detail"),
    path("gallery/", views.GalleryView.as_view(), name="gallery"),
    path("contact/", views.ContactView.as_view(), name="contact"),
]
