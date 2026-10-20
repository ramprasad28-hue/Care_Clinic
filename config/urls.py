"""Root URL configuration."""
from django.conf import settings
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
    # Role-based dashboards (landing routes each user to their role's view).
    path("dashboard/", include("dashboards.urls")),
]

# Development-only serving of administrator-uploaded media (ADR-022). The
# block is skipped entirely when settings.DEBUG is False, so no production
# configuration can accidentally expose the media directory from Django:
# in a real deployment MEDIA_URL is served by the web server/object storage
# layer and MEDIA_ROOT lives on a persistent volume (deployment decision —
# see docs/phase-c1-admin-managed-imagery-plan.md §3).
if settings.DEBUG:
    from django.conf.urls.static import static as static_url_patterns

    urlpatterns += static_url_patterns(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
