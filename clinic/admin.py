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
from datetime import date, timedelta


from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponseNotAllowed, JsonResponse
from django.urls import path
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .forms import (
    AvailabilityRuleForm,
    DoctorAdminForm,
    DoctorLeaveForm,
    SpecialityAdminForm,
)
from .models import AvailabilityRule, Doctor, DoctorLeave, Speciality, Weekday

User = get_user_model()

# Hard cap on the span a calendar "load events" request may cover. Bigger
# windows are clamped so a crafted query cannot ask the server to expand an
# unbounded number of recurring occurrences.
SCHEDULE_MAX_RANGE_DAYS = 62


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


def _iso_date_or_none(value):
    """Strict ISO-8601 date parsing for schedule endpoint parameters."""
    if not value:
        return None
    try:
        return date.fromisoformat(str(value).strip())
    except ValueError:
        return None


def _time_str(value):
    return value.strftime("%H:%M") if value is not None else None


def _rule_to_dict(rule):
    """JSON shape for one AvailabilityRule as returned by the endpoints."""
    return {
        "kind": "availability",
        "id": rule.pk,
        "weekday": rule.weekday,
        "weekday_label": rule.get_weekday_display(),
        "start": _time_str(rule.start_time),
        "end": _time_str(rule.end_time),
        "slot_length_minutes": rule.slot_length_minutes,
        "effective_slot_length_minutes": rule.effective_slot_length_minutes,
        "is_active": rule.is_active,
    }


def _leave_to_dict(leave):
    """JSON shape for one DoctorLeave as returned by the endpoints."""
    return {
        "kind": "leave",
        "id": leave.pk,
        "start_date": leave.start_date.isoformat(),
        "end_date": leave.end_date.isoformat(),
        "reason": leave.reason,
    }


def _availability_occurrences(rules, start_date, end_date):
    """Materialize one occurrence per matching weekday in ``[start, end]``.

    ``AvailabilityRule`` is recurring weekly, so a Monday 09:00-13:00 rule
    yields one entry for every Monday in the requested window. This keeps the
    client dumb: it renders concrete dates and never has to invent recurrence
    (avoiding client-side weekday/date mismatches).
    """
    occurrences = []
    day = start_date
    while day <= end_date:
        for rule in rules:
            if rule.weekday == day.weekday():
                occurrence = _rule_to_dict(rule)
                occurrence.update(
                    {
                        "rule_id": rule.pk,
                        "date": day.isoformat(),
                    }
                )
                occurrences.append(occurrence)
        day += timedelta(days=1)
    return occurrences


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

    def get_fields(self, request, obj=None):
        """Add the dual account-mode fields to the admin's computed fieldsets.

        ``ModelAdmin.get_fields`` derives the rendered fields from
        ``form.base_fields`` (class-level), while DoctorAdminForm adds its
        account-mode fields per-instance (add requests only, renamed on
        change). Extend the computed field list here so the selector and the
        provisioned-account inputs render on the Add page, in a predictable
        order, and stay absent when editing an existing Doctor.
        """
        fields = list(super().get_fields(request, obj))
        add_only = list(DoctorAdminForm.add_only_field_names)
        if obj is not None:
            # Change mode: DoctorAdminForm drops these per-instance; strip
            # them from the computed field list to match.
            return [f for f in fields if f not in add_only]
        fields = [f for f in fields if f not in add_only]
        # Toolbar order for a natural flow: mode selector, existing-user
        # picker, provisioned-account fields, then the doctor profile fields.
        if "user" in fields:
            fields.remove("user")
        return ["account_mode", "user", *DoctorAdminForm.new_account_field_names, *fields]

    # ------------------------------------------------------------------
    # Scheduling calendar (administrative JSON API)
    # ------------------------------------------------------------------
    # Django admin views already require an authenticated staff session;
    # each handler additionally enforces the AdministratorOnlyMixin rule
    # (_is_administrator) before touching data. Writes go through POST with
    # Django's CSRF middleware and reuse the regular ModelForms so model
    # validation (overlaps, date ordering, positive durations) is never
    # bypassed — the calendar is never the scheduling source of truth.
    change_form_template = "admin/clinic/doctor/change_form.html"

    def get_urls(self):
        url_patterns = super().get_urls()
        info = (self.model._meta.app_label, self.model._meta.model_name)
        return [
            path(
                "<int:object_id>/schedule/events/",
                self.admin_site.admin_view(self.schedule_events_view),
                name=f"{info[0]}_{info[1]}_schedule_events",
            ),
            path(
                "<int:object_id>/schedule/availability/create/",
                self.admin_site.admin_view(self.schedule_availability_create_view),
                name=f"{info[0]}_{info[1]}_schedule_availability_create",
            ),
            path(
                "<int:object_id>/schedule/availability/<int:rule_id>/update/",
                self.admin_site.admin_view(self.schedule_availability_update_view),
                name=f"{info[0]}_{info[1]}_schedule_availability_update",
            ),
            path(
                "<int:object_id>/schedule/availability/<int:rule_id>/delete/",
                self.admin_site.admin_view(self.schedule_availability_delete_view),
                name=f"{info[0]}_{info[1]}_schedule_availability_delete",
            ),
            path(
                "<int:object_id>/schedule/leave/create/",
                self.admin_site.admin_view(self.schedule_leave_create_view),
                name=f"{info[0]}_{info[1]}_schedule_leave_create",
            ),
            path(
                "<int:object_id>/schedule/leave/<int:leave_id>/update/",
                self.admin_site.admin_view(self.schedule_leave_update_view),
                name=f"{info[0]}_{info[1]}_schedule_leave_update",
            ),
            path(
                "<int:object_id>/schedule/leave/<int:leave_id>/delete/",
                self.admin_site.admin_view(self.schedule_leave_delete_view),
                name=f"{info[0]}_{info[1]}_schedule_leave_delete",
            ),
            *url_patterns,
        ]

    def _schedule_gate(self, request, object_id=None):
        """Common guard: administrator + existing Doctor row (404 otherwise)."""
        if not _is_administrator(request.user):
            raise PermissionDenied(_("Only administrators can manage doctor schedules."))
        if object_id is not None:
            doctor = self.get_object(request, str(object_id))
            if doctor is None:
                raise Http404("No doctor found with the given id.")
            return doctor
        return None

    def _method_gate(self, request, allowed):
        """Reject disallowed HTTP verbs with a 405.

        These schedule views are bound instance methods, so the
        ``django.views.decorators.http.require_*`` decorators cannot be used:
        the URL dispatcher would bind ``self`` into the decorator's positional
        ``request`` parameter. Enforce the allowed verbs here instead.
        """
        if request.method not in allowed:
            return HttpResponseNotAllowed(allowed)
        return None

    def schedule_events_view(self, request, object_id):
        if (response := self._method_gate(request, ("GET",))) is not None:
            return response
        doctor = self._schedule_gate(request, object_id)
        start = _iso_date_or_none(request.GET.get("start"))
        end = _iso_date_or_none(request.GET.get("end"))
        if start is None or end is None:
            return JsonResponse(
                {"errors": {"__all__": ["A valid start and end ISO date are required."]}},
                status=400,
            )
        if end < start:
            start, end = end, start
        if (end - start).days > SCHEDULE_MAX_RANGE_DAYS:
            end = start + timedelta(days=SCHEDULE_MAX_RANGE_DAYS)

        rules = list(AvailabilityRule.objects.filter(doctor=doctor))
        leaves = list(
            DoctorLeave.objects.filter(
                doctor=doctor, start_date__lte=end, end_date__gte=start
            )
        )
        return JsonResponse(
            {
                "doctor": {
                    "id": doctor.pk,
                    "name": doctor.user.get_full_name() or doctor.user.email,
                    "default_slot_length_minutes": doctor.slot_length_minutes,
                },
                "start": start.isoformat(),
                "end": end.isoformat(),
                # Recurring availability, already expanded to concrete dates.
                "occurrences": _availability_occurrences(rules, start, end),
                "rules": [_rule_to_dict(rule) for rule in rules],
                # Date-specific leave ranges (inclusive).
                "leaves": [_leave_to_dict(leave) for leave in leaves],
            }
        )

    # -- AvailabilityRule ---------------------------------------------
    def _availability_by_doctor(self, doctor, rule_id):
        rule = AvailabilityRule.objects.filter(doctor=doctor, pk=rule_id).first()
        if rule is None:
            raise Http404("No availability rule for this doctor with the given id.")
        return rule

    def schedule_availability_create_view(self, request, object_id):
        if (response := self._method_gate(request, ("POST",))) is not None:
            return response
        doctor = self._schedule_gate(request, object_id)
        form = AvailabilityRuleForm(request.POST)
        if form.is_valid():
            rule = form.save(commit=False)
            rule.doctor_id = doctor.pk  # never trusted from the client
            try:
                rule.save()  # full_clean(): window order, overlap, duration
            except ValidationError as exc:
                return JsonResponse(
                    {"errors": exc.message_dict}, status=400
                )
            return JsonResponse({"status": "ok", "rule": _rule_to_dict(rule)}, status=201)
        return JsonResponse({"errors": dict(form.errors)}, status=400)

    def schedule_availability_update_view(self, request, object_id, rule_id):
        if (response := self._method_gate(request, ("POST",))) is not None:
            return response
        doctor = self._schedule_gate(request, object_id)
        rule = self._availability_by_doctor(doctor, rule_id)
        form = AvailabilityRuleForm(request.POST, instance=rule)
        if form.is_valid():
            rule = form.save(commit=False)
            try:
                rule.save()  # full_clean(): window order, overlap, duration
            except ValidationError as exc:
                return JsonResponse({"errors": exc.message_dict}, status=400)
            return JsonResponse({"status": "ok", "rule": _rule_to_dict(rule)})
        return JsonResponse({"errors": dict(form.errors)}, status=400)

    def schedule_availability_delete_view(self, request, object_id, rule_id):
        if (response := self._method_gate(request, ("POST",))) is not None:
            return response
        doctor = self._schedule_gate(request, object_id)
        rule = self._availability_by_doctor(doctor, rule_id)
        rule.delete()
        # Existing AppointmentSlot rows (including BOOKED ones) are never
        # touched here: slot generation materializes the schedule, and only
        # it decides what exists going forward.
        return JsonResponse({"status": "ok"})

    # -- DoctorLeave ---------------------------------------------------
    def _leave_by_doctor(self, doctor, leave_id):
        leave = DoctorLeave.objects.filter(doctor=doctor, pk=leave_id).first()
        if leave is None:
            raise Http404("No leave entry for this doctor with the given id.")
        return leave

    def schedule_leave_create_view(self, request, object_id):
        if (response := self._method_gate(request, ("POST",))) is not None:
            return response
        doctor = self._schedule_gate(request, object_id)
        form = DoctorLeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.doctor_id = doctor.pk  # never trusted from the client
            try:
                leave.save()  # full_clean(): start/end ordering
            except ValidationError as exc:
                return JsonResponse({"errors": exc.message_dict}, status=400)
            return JsonResponse({"status": "ok", "leave": _leave_to_dict(leave)}, status=201)
        return JsonResponse({"errors": dict(form.errors)}, status=400)

    def schedule_leave_update_view(self, request, object_id, leave_id):
        if (response := self._method_gate(request, ("POST",))) is not None:
            return response
        doctor = self._schedule_gate(request, object_id)
        leave = self._leave_by_doctor(doctor, leave_id)
        form = DoctorLeaveForm(request.POST, instance=leave)
        if form.is_valid():
            leave = form.save(commit=False)
            try:
                leave.save()  # full_clean(): start/end ordering
            except ValidationError as exc:
                return JsonResponse({"errors": exc.message_dict}, status=400)
            return JsonResponse({"status": "ok", "leave": _leave_to_dict(leave)})
        return JsonResponse({"errors": dict(form.errors)}, status=400)

    def schedule_leave_delete_view(self, request, object_id, leave_id):
        if (response := self._method_gate(request, ("POST",))) is not None:
            return response
        doctor = self._schedule_gate(request, object_id)
        leave = self._leave_by_doctor(doctor, leave_id)
        leave.delete()
        return JsonResponse({"status": "ok"})


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
