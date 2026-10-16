"""Django admin for the clinic app with backend-enforced authorization.

Django admin already requires ``is_staff`` to log in, but this module adds
explicit, per-model backend checks so authorization does not rely on hidden
navigation links:

* ``Speciality`` and ``Doctor`` are **administrator-only** (ADMIN role or
  superuser) for view/add/change/delete.
* ``AvailabilityRule`` and ``DoctorLeave`` give administrators full access but
  let a DOCTOR see and edit **only their own** records: the changelist queryset
  is scoped to ``doctor__user=request.user`` and ``save_model`` forces ownership
  from the session, so a submitted doctor id cannot be used to hijack another
  doctor's records.
"""
from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import AvailabilityRule, Doctor, DoctorLeave, Speciality

User = get_user_model()


def _is_administrator(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and (user.is_superuser or getattr(user, "role", None) == User.Role.ADMIN)
    )


def _is_doctor(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and getattr(user, "role", None) == User.Role.DOCTOR
    )


def _owns(user, obj):
    """True if ``obj`` belongs to ``user``'s doctor profile."""
    doctor = getattr(user, "doctor", None)
    return doctor is not None and obj.doctor_id == doctor.pk


class AdministratorOnlyMixin:
    """Restrict an entire ModelAdmin to administrators (ADMIN role/superuser)."""

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


class DoctorOwnedAdminMixin:
    """Administrators see everything; doctors see and edit only their own rows."""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if _is_administrator(request.user):
            return qs
        if _is_doctor(request.user):
            return qs.filter(doctor__user=request.user)
        return qs.none()

    def has_module_permission(self, request):
        return _is_administrator(request.user) or _is_doctor(request.user)

    def has_view_permission(self, request, obj=None):
        if _is_administrator(request.user):
            return True
        if _is_doctor(request.user):
            return obj is None or _owns(request.user, obj)
        return False

    def has_add_permission(self, request):
        return _is_administrator(request.user) or _is_doctor(request.user)

    def has_change_permission(self, request, obj=None):
        if _is_administrator(request.user):
            return True
        if _is_doctor(request.user):
            return obj is None or _owns(request.user, obj)
        return False

    def has_delete_permission(self, request, obj=None):
        if _is_administrator(request.user):
            return True
        if _is_doctor(request.user):
            return obj is None or _owns(request.user, obj)
        return False

    def save_model(self, request, obj, form, change):
        # Force ownership for doctors so a submitted doctor id cannot redirect
        # the write to another doctor's records.
        if _is_doctor(request.user) and not _is_administrator(request.user):
            doctor = getattr(request.user, "doctor", None)
            if doctor is not None:
                obj.doctor = doctor
        super().save_model(request, obj, form, change)


class AvailabilityRuleInline(admin.TabularInline):
    model = AvailabilityRule
    extra = 1
    fields = ("weekday", "start_time", "end_time", "slot_length_minutes", "is_active")


class DoctorLeaveInline(admin.TabularInline):
    model = DoctorLeave
    extra = 1
    fields = ("start_date", "end_date", "reason")


@admin.register(Speciality)
class SpecialityAdmin(AdministratorOnlyMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "doctor_count", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")

    @admin.display(description="Doctors")
    def doctor_count(self, obj):
        return obj.doctors.count()


@admin.register(Doctor)
class DoctorAdmin(AdministratorOnlyMixin, admin.ModelAdmin):
    list_display = (
        "full_name",
        "speciality",
        "registration_number",
        "is_accepting_appointments",
        "user_is_active",
        "updated_at",
    )
    list_filter = ("speciality", "is_accepting_appointments", "user__is_active")
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "registration_number",
        "qualification",
    )
    autocomplete_fields = ("user", "speciality")
    ordering = ("user__first_name", "user__last_name")
    list_select_related = ("user", "speciality")
    readonly_fields = ("created_at", "updated_at", "slug")
    inlines = [AvailabilityRuleInline, DoctorLeaveInline]

    @admin.display(description="Name", ordering="user__first_name")
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.email

    @admin.display(description="User active", boolean=True, ordering="user__is_active")
    def user_is_active(self, obj):
        return obj.user.is_active


@admin.register(AvailabilityRule)
class AvailabilityRuleAdmin(DoctorOwnedAdminMixin, admin.ModelAdmin):
    list_display = (
        "doctor",
        "weekday",
        "start_time",
        "end_time",
        "slot_length_minutes",
        "is_active",
    )
    list_filter = ("weekday", "is_active")
    search_fields = ("doctor__user__email", "doctor__user__first_name")
    ordering = ("doctor", "weekday", "start_time")
    list_select_related = ("doctor", "doctor__user")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DoctorLeave)
class DoctorLeaveAdmin(DoctorOwnedAdminMixin, admin.ModelAdmin):
    list_display = ("doctor", "start_date", "end_date", "reason", "created_at")
    list_filter = ("doctor",)
    search_fields = ("doctor__user__email", "reason")
    ordering = ("-start_date",)
    list_select_related = ("doctor", "doctor__user")
    readonly_fields = ("created_at",)
