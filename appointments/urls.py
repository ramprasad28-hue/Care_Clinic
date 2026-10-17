"""Appointment URLs, namespaced as ``appointments:*``."""
from django.urls import path

from . import views

app_name = "appointments"

urlpatterns = [
    path("", views.AppointmentListView.as_view(), name="list"),
    path("book/<slug:slug>/", views.BookAppointmentView.as_view(), name="book"),
    path("<str:reference>/", views.AppointmentDetailView.as_view(), name="detail"),
    path("<str:reference>/cancel/", views.CancelAppointmentView.as_view(), name="cancel"),
    path(
        "<str:reference>/reschedule/",
        views.RescheduleAppointmentView.as_view(),
        name="reschedule",
    ),
]
