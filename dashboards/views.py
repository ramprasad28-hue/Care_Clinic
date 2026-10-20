"""Role-based dashboards.

Design (see ``docs/decisions.md`` ADR-019):

* **One landing route** (``dashboards:landing``) maps an authenticated user to
  the dashboard matching their role and redirects there. The role always comes
  from the session user — never from the request body — and an unrecognised role
  renders a safe informational page instead of erroring.
* Each dashboard is gated by :class:`accounts.permissions.RoleRequiredMixin`
  (anonymous -> login redirect; wrong role -> HTTP 403).
* Appointment records are resolved through ``Appointment.objects.for_user`` and
  the doctor dashboard is additionally scoped to the caller's own ``Doctor``
  profile, so a foreign reference yields **404** (IDOR prevention).
* Every state change is a POST that delegates to :mod:`appointments.services`
  (the transactional layer); views never mutate a status field directly.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.generic import TemplateView

from accounts.models import User
from accounts.permissions import RoleRequiredMixin
from appointments import services
from appointments.models import (
    ALLOWED_TRANSITIONS,
    Appointment,
    AppointmentStatus,
)
from appointments.selectors import available_dates, available_slots
from clinic.models import Doctor

from . import selectors
from .forms import AppointmentFilterForm, ReceptionBookingForm

Role = User.Role

#: Terminal statuses that no dashboard action should offer.
_ACTION_EXCLUDED = {AppointmentStatus.CANCELLED}


def dashboard_url_name(user):
    """Return the URL name of the dashboard ``user`` belongs on, or ``None``."""
    if getattr(user, "is_superuser", False) or user.role == Role.ADMIN:
        return "dashboards:admin"
    if user.role == Role.DOCTOR:
        return "dashboards:doctor"
    if user.role == Role.RECEPTIONIST:
        return "dashboards:receptionist"
    if user.role == Role.PATIENT:
        return "dashboards:patient"
    return None


def _attach_actions(appointments, actor):
    """Annotate each appointment with the status actions ``actor`` may perform.

    Avoids per-row template lookups and keeps the decision in the service layer
    (``can_update_status`` is re-checked inside ``transition_status``).
    """
    for appointment in appointments:
        manageable = services.can_update_status(appointment, actor)
        appointment.can_manage = manageable
        if manageable:
            appointment.allowed_actions = [
                (status, AppointmentStatus(status).label)
                for status in sorted(
                    ALLOWED_TRANSITIONS.get(appointment.status, set()) - _ACTION_EXCLUDED,
                    key=lambda s: s.value,
                )
            ]
        else:
            appointment.allowed_actions = []
    return appointments


def _safe_redirect(request, fallback="dashboards:landing"):
    """Redirect to a same-host ``next`` if present, else ``fallback``."""
    target = request.POST.get("next") or request.GET.get("next")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(target)
    return redirect(fallback)


class DashboardLandingView(LoginRequiredMixin, View):
    """Route an authenticated user to the dashboard for their role."""

    def get(self, request):
        url_name = dashboard_url_name(request.user)
        if url_name is None:
            return render(request, "dashboards/no_dashboard.html", status=200)
        return redirect(url_name)


class PatientDashboardView(RoleRequiredMixin, TemplateView):
    """A patient's own upcoming appointments, history and quick actions."""

    allowed_roles = (Role.PATIENT,)
    template_name = "dashboards/patient_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        base = (
            Appointment.objects.for_user(user)
            .select_related("doctor__user", "doctor__speciality", "patient", "slot")
        )
        today = timezone.localdate()
        upcoming = (
            base.filter(date__gte=today).active().order_by("date", "start_time")[:10]
        )
        history = base.filter(date__lt=today).order_by("-date", "-start_time")[:10]
        _attach_actions(upcoming, user)
        _attach_actions(history, user)
        context.update({"upcoming": upcoming, "history": history})
        return context


class DoctorDashboardView(RoleRequiredMixin, TemplateView):
    """A doctor's own schedule: today, upcoming and past appointments."""

    allowed_roles = (Role.DOCTOR,)
    template_name = "dashboards/doctor_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        doctor = getattr(user, "doctor", None)
        context["doctor"] = doctor

        if doctor is None:
            context.update({"today": [], "upcoming": [], "past": []})
            return context

        base = (
            Appointment.objects.for_user(user)
            .filter(doctor=doctor)
            .select_related("doctor__user", "doctor__speciality", "patient", "slot")
        )
        today = timezone.localdate()
        today_items = base.filter(date=today).order_by("start_time")
        upcoming = (
            base.filter(date__gt=today).order_by("date", "start_time")[:15]
        )
        past = base.filter(date__lt=today).order_by("-date", "-start_time")[:15]
        for group in (today_items, upcoming, past):
            _attach_actions(group, user)
        context.update({"today": today_items, "upcoming": upcoming, "past": past})
        return context


class _FilteredAppointmentDashboard(RoleRequiredMixin, TemplateView):
    """Shared filtering/pagination plumbing for the staff dashboards."""

    filter_fields = None
    template_name = "dashboards/receptionist_dashboard.html"

    def get_queryset(self, user):
        return (
            Appointment.objects.for_user(user)
            .select_related("doctor__user", "doctor__speciality", "patient", "slot")
            .order_by("date", "start_time")
        )

    def build_filter(self, request):
        form = AppointmentFilterForm(request.GET, fields=self.filter_fields)
        if form.is_valid():
            return form, form.cleaned_data
        return form, {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        form, data = self.build_filter(request)
        queryset = selectors.filter_appointments(
            self.get_queryset(request.user),
            scope=data.get("scope") or "upcoming",
            date=data.get("date"),
            status=data.get("status"),
            doctor=data.get("doctor"),
            patient=data.get("patient"),
            reference=data.get("reference"),
        )
        page_obj = selectors.paginate(queryset, request)
        _attach_actions(page_obj.object_list, request.user)
        context.update(
            {
                "filter_form": form,
                "page_obj": page_obj,
                "appointments": page_obj.object_list,
                "querystring": selectors.querystring_without_page(request),
                "show_actions": True,
            }
        )
        return context


class ReceptionistDashboardView(_FilteredAppointmentDashboard):
    """Clinic-wide booking overview for receptionists (all appointments)."""

    allowed_roles = (Role.RECEPTIONIST,)
    template_name = "dashboards/receptionist_dashboard.html"
    filter_fields = ("scope", "date", "status", "doctor", "patient", "reference")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        user = self.request.user
        base = Appointment.objects.for_user(user)
        context["today_count"] = base.filter(date=today).count()
        context["upcoming_count"] = base.filter(date__gte=today).count()
        return context


class ReceptionBookView(RoleRequiredMixin, View):
    """Receptionist books a slot on behalf of a patient."""

    allowed_roles = (Role.RECEPTIONIST,)
    template_name = "dashboards/receptionist_book.html"

    def _resolve_doctor(self, raw):
        """Resolve a submitted doctor id safely (never trust it blindly)."""
        try:
            return Doctor.objects.select_related("user").filter(pk=int(raw)).first()
        except (TypeError, ValueError):
            return None

    def _resolve_patient(self, raw):
        """Resolve a submitted patient id safely (must be a PATIENT)."""
        if raw is None or not str(raw).isdigit():
            return None
        return User.objects.filter(role=Role.PATIENT, pk=raw).first()

    def _render(self, request, *, form, selected_patient, selected_doctor, day):
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "patients": User.objects.filter(role=Role.PATIENT).order_by(
                    "first_name", "email"
                ),
                "doctors": Doctor.objects.select_related("user").order_by(
                    "user__first_name", "user__email"
                ),
                "selected_patient": selected_patient,
                "selected_doctor": selected_doctor,
                "selected_day": day or timezone.localdate(),
                "dates": available_dates(selected_doctor, days=21)
                if selected_doctor
                else [],
                "slots": available_slots(selected_doctor, day)
                if selected_doctor and day
                else [],
            },
        )

    def get(self, request):
        selected_doctor = self._resolve_doctor(request.GET.get("doctor"))
        selected_patient = self._resolve_patient(request.GET.get("patient"))
        day = selectors.parse_date(request.GET.get("date")) or timezone.localdate()
        initial = {
            "patient": selected_patient.pk if selected_patient else None,
            "doctor": selected_doctor.pk if selected_doctor else None,
            "date": day,
        }
        form = ReceptionBookingForm(
            doctor=selected_doctor, day=day, initial=initial
        )
        return self._render(
            request,
            form=form,
            selected_patient=selected_patient,
            selected_doctor=selected_doctor,
            day=day,
        )

    def post(self, request):
        day = selectors.parse_date(request.POST.get("date"))
        selected_doctor = self._resolve_doctor(request.POST.get("doctor"))
        selected_patient = self._resolve_patient(request.POST.get("patient"))
        form = ReceptionBookingForm(request.POST, doctor=selected_doctor, day=day)
        if form.is_valid():
            try:
                appointment = services.book_slot(
                    int(form.cleaned_data["slot"]),
                    actor=request.user,
                    patient=form.cleaned_data["patient"],
                    reason=form.cleaned_data.get("reason", ""),
                    doctor=form.cleaned_data["doctor"],
                )
            except services.BookingError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request,
                    f"Booked {appointment.reference} for "
                    f"{appointment.patient.get_full_name()}.",
                )
                return redirect("appointments:detail", reference=appointment.reference)
        else:
            messages.error(
                request, "Please choose a patient, a doctor and an available slot."
            )
        return self._render(
            request,
            form=form,
            selected_patient=selected_patient,
            selected_doctor=selected_doctor,
            day=day,
        )


class AdminDashboardView(RoleRequiredMixin, TemplateView):
    """Clinic-wide statistics plus a filterable appointment list."""

    allowed_roles = (Role.ADMIN,)
    template_name = "dashboards/admin_dashboard.html"
    filter_fields = ("scope", "date", "status", "doctor", "patient", "reference")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        today = timezone.localdate()
        user = request.user
        base = Appointment.objects.for_user(user)

        aggregate = base.aggregate(
            total=Count("id"),
            today=Count("id", filter=Q(date=today)),
            upcoming=Count("id", filter=Q(date__gte=today)),
            completed=Count("id", filter=Q(status=AppointmentStatus.COMPLETED)),
            cancelled=Count("id", filter=Q(status=AppointmentStatus.CANCELLED)),
        )
        by_status = {
            row["status"]: row["count"]
            for row in base.values("status").annotate(count=Count("id"))
        }
        status_breakdown = [
            {
                "value": value,
                "label": label,
                "count": by_status.get(value, 0),
            }
            for value, label in AppointmentStatus.choices
        ]

        form = AppointmentFilterForm(request.GET, fields=self.filter_fields)
        data = form.cleaned_data if form.is_valid() else {}
        queryset = selectors.filter_appointments(
            Appointment.objects.for_user(request.user).select_related(
                "doctor__user", "patient"
            ),
            scope=data.get("scope") or "upcoming",
            date=data.get("date"),
            status=data.get("status"),
            doctor=data.get("doctor"),
            patient=data.get("patient"),
            reference=data.get("reference"),
        ).order_by("date", "start_time")
        page_obj = selectors.paginate(queryset, request)
        _attach_actions(page_obj.object_list, request.user)

        context.update(
            {
                "stats": aggregate,
                "status_breakdown": status_breakdown,
                "total_patients": User.objects.filter(role=Role.PATIENT).count(),
                "total_doctors": Doctor.objects.count(),
                "by_status": by_status,
                "filter_form": form,
                "page_obj": page_obj,
                "appointments": page_obj.object_list,
                "querystring": selectors.querystring_without_page(request),
                "show_actions": True,
            }
        )
        return context


class AppointmentStatusUpdateView(LoginRequiredMixin, View):
    """Apply a permitted status transition (POST only, CSRF-protected)."""

    def post(self, request, reference):
        appointment = get_object_or_404(
            Appointment.objects.for_user(request.user), reference=reference
        )
        if not services.can_update_status(appointment, request.user):
            raise PermissionDenied("You are not allowed to change this status.")

        new_status = request.POST.get("new_status")
        if new_status not in dict(AppointmentStatus.choices):
            messages.error(request, "Unknown status requested.")
            return _safe_redirect(request)

        try:
            services.transition_status(
                appointment.pk, actor=request.user, new_status=new_status
            )
        except services.BookingError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(
                request,
                f"{appointment.reference} marked {AppointmentStatus(new_status).label}.",
            )
        return _safe_redirect(request)
