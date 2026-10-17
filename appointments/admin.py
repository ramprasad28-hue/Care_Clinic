"""Django admin for slots and appointments.

Django admin already requires ``is_staff``. On top of that, this module limits
the appointment models to administrators (ADMIN role or superuser) so
authorization never relies on hidden navigation.
"""
from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Appointment, AppointmentSlot

User = get_user_model()


def _is_administrator(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and (user.is_superuser or getattr(user, "role", None) == User.Role.ADMIN)
    )


class AdministratorOnlyMixin:
    def has_module_permission(self, request):
        return _is_administrator(request.user)

    def has_view_permission(self, request, obj=None):
        return _is_administrator(request.user)

    def has_add_permission(self, request):
        return _is_administrator(request.user)

    def has_change_permission(self, request, obj=None):
        return _is_administrator(request.user)

    def has_delete_permission(self, request, obj=None):
        return _is_administrator(request.user)


@admin.register(AppointmentSlot)
class AppointmentSlotAdmin(AdministratorOnlyMixin, admin.ModelAdmin):
    list_display = ("doctor", "date", "start_time", "end_time", "status")
    list_filter = ("status", "date", "doctor")
    search_fields = ("doctor__user__email", "doctor__user__first_name")
    date_hierarchy = "date"
    ordering = ("-date", "start_time")
    list_select_related = ("doctor", "doctor__user")
    readonly_fields = ("created_at",)


@admin.register(Appointment)
class AppointmentAdmin(AdministratorOnlyMixin, admin.ModelAdmin):
    list_display = (
        "reference",
        "patient",
        "doctor",
        "date",
        "start_time",
        "status",
    )
    list_filter = ("status", "date", "doctor")
    search_fields = (
        "reference",
        "patient__email",
        "doctor__user__email",
    )
    date_hierarchy = "date"
    ordering = ("-date", "-start_time")
    list_select_related = ("patient", "doctor", "doctor__user", "slot")
    readonly_fields = ("reference", "created_at", "updated_at")
    autocomplete_fields = ("patient", "doctor", "slot", "booked_by", "cancelled_by")
