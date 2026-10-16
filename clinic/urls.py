"""Doctor self-service URLs (availability and leave), namespaced as ``clinic:*``."""
from django.urls import path

from . import views

app_name = "clinic"

urlpatterns = [
    path("doctor/availability/", views.AvailabilityListView.as_view(), name="availability_list"),
    path("doctor/availability/add/", views.AvailabilityCreateView.as_view(), name="availability_add"),
    path(
        "doctor/availability/<int:pk>/edit/",
        views.AvailabilityUpdateView.as_view(),
        name="availability_edit",
    ),
    path(
        "doctor/availability/<int:pk>/delete/",
        views.AvailabilityDeleteView.as_view(),
        name="availability_delete",
    ),
    path("doctor/leave/", views.LeaveListView.as_view(), name="leave_list"),
    path("doctor/leave/add/", views.LeaveCreateView.as_view(), name="leave_add"),
    path(
        "doctor/leave/<int:pk>/delete/",
        views.LeaveDeleteView.as_view(),
        name="leave_delete",
    ),
]
