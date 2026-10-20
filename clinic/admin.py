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
* Image uploads (ADR-022, C1): ``Speciality.image`` / ``Doctor.profile_image``
  are administrator-managed uploads with preview widgets; dimension/ratio
  guidance is surfaced as warnings after a successful save.
"""
from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .forms import DoctorAdminForm, SpecialityAdminForm
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


class ImageWarningAdminMixin:
    """Surface form-reported image warnings after a successful save (ADR-022).

    Dimension/ratio observations never block an otherwise valid upload (plan
    rule: prefer warnings over rejections); they surface here as non-fatal
    admin messages.
    """

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        for warning in getattr(form, "image_warnings", []):
            self.message_user(request, warning, level=messages.WARNING)


class AvailabilityRuleInline(admin.TabularInline):
    model = AvailabilityRule
    extra = 1
    fields = ("weekday", "start_time", "end_time", "slot_length_minutes", "is_active")


class DoctorLeaveInline(admin.TabularInline):
    model = DoctorLeave
    extra = 1
    fields = ("start_date", "end_date", "reason")


def _media_src(image_field_file):
    """Usable media URL for an upload, or "" when nothing is set/cleared."""
    if not image_field_file:
        return ""
    try:
        return image_field_file.url
    except ValueError:
        return ""


@admin.register(Speciality)
class SpecialityAdmin(ImageWarningAdminMixin, AdministratorOnlyMixin, admin.ModelAdmin):
    form = SpecialityAdminForm
    list_display = ("name", "slug", "image_thumb", "is_active", "doctor_count", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    readonly_fields = ("image_preview", "created_at", "updated_at")

    def image_thumb(self, obj):
        src = _media_src(obj.image)
        if not src:
            return "—"
        return format_html('<img src="{}" style="max-height:52px;border-radius:4px" alt="">', src)
    image_thumb.short_description = _("Image")

    @admin.display(description=_("Current image"))
    def image_preview(self, obj):
        src = _media_src(obj.image)
        if not src:
            return _("No image uploaded — the static fallback (if any) is shown on the site.")
        return format_html(
            '<img src="{}" style="max-height:140px;border-radius:6px" alt="">', src
        )

    @admin.display(description="Doctors")
    def doctor_count(self, obj):
        return obj.doctors.count()


@admin.register(Doctor)
class DoctorAdmin(ImageWarningAdminMixin, AdministratorOnlyMixin, admin.ModelAdmin):
    form = DoctorAdminForm
    list_display = (
        "full_name",
        "speciality",
        "portrait_thumb",
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
    readonly_fields = ("portrait_preview", "created_at", "updated_at", "slug")
    inlines = [AvailabilityRuleInline, DoctorLeaveInline]

    def portrait_thumb(self, obj):
        src = _media_src(obj.profile_image)
        if not src:
            return "—"
        return format_html('<img src="{}" style="max-height:52px;border-radius:4px" alt="">', src)
    portrait_thumb.short_description = _("Portrait")

    @admin.display(description=_("Current portrait"))
    def portrait_preview(self, obj):
        src = _media_src(obj.profile_image)
        if not src:
            return _(
                "No portrait uploaded — the static placeholder or initials avatar is shown on the site."
            )
        return format_html(
            '<img src="{}" style="max-height:140px;border-radius:6px" alt="">', src
        )

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
