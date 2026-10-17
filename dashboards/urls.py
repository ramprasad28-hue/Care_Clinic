"""Dashboard URLs, namespaced as ``dashboards:*``."""
from django.urls import path

from . import views

app_name = "dashboards"

urlpatterns = [
    path("", views.DashboardLandingView.as_view(), name="landing"),
    path("patient/", views.PatientDashboardView.as_view(), name="patient"),
    path("doctor/", views.DoctorDashboardView.as_view(), name="doctor"),
    path(
        "receptionist/",
        views.ReceptionistDashboardView.as_view(),
        name="receptionist",
    ),
    path(
        "receptionist/book/",
        views.ReceptionBookView.as_view(),
        name="receptionist_book",
    ),
    path("admin/", views.AdminDashboardView.as_view(), name="admin"),
    path(
        "appointments/<str:reference>/status/",
        views.AppointmentStatusUpdateView.as_view(),
        name="appointment_status",
    ),
]
