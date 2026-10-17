"""Root URL configuration."""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Public site (home + specialities + doctors). Included without a
    # namespace so the project-wide "home" route name is preserved.
    path("", include("website.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    # Doctor self-service (availability & leave), namespaced as clinic:*.
    path("clinic/", include("clinic.urls")),
    # Appointment booking + patient/doctor appointment pages.
    path("appointments/", include("appointments.urls")),
]
