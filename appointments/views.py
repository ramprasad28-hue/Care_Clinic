"""Server-rendered booking views.

Authorization model:

* Slot browsing / booking is patient-only (``RoleRequiredMixin``); anonymous
  users are redirected to login.
* Appointment list/detail/cancel/reschedule always resolve the record through
  ``Appointment.objects.for_user`` so an id/reference belonging to someone else
  yields **404** (IDOR prevention).
* Permission to *cancel* / *reschedule* is decided by
  :mod:`appointments.services` predicates (and re-checked inside the service).
"""
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView

from accounts.models import User
from accounts.permissions import RoleRequiredMixin
from clinic.models import Doctor

from . import services
from .forms import BookingForm, CancelForm, RescheduleForm
from .models import Appointment
from .selectors import available_dates, available_slots


def _parse_day(value, default):
    if value:
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return default
    return default


def _scoped_appointment(request, reference):
    return get_object_or_404(
        Appointment.objects.for_user(request.user).select_related(
            "doctor__user", "patient", "slot"
        ),
        reference=reference,
    )


class BookAppointmentView(RoleRequiredMixin, View):
    """Patient slot picker + booking form for a single doctor."""

    allowed_roles = (User.Role.PATIENT,)
    template_name = "appointments/appointment_book.html"

    def _get_doctor(self, slug):
        return get_object_or_404(Doctor.objects.public(), slug=slug)

    def _render(self, request, doctor, form, day):
        dates = available_dates(doctor, days=21)
        if day is None:
            day = dates[0] if dates else timezone.localdate()
        return render(
            request,
            self.template_name,
            {
                "doctor": doctor,
                "form": form,
                "dates": dates,
                "selected_day": day,
                "slots": available_slots(doctor, day),
            },
        )

    def get(self, request, slug):
        doctor = self._get_doctor(slug)
        dates = available_dates(doctor, days=21)
        day = _parse_day(request.GET.get("date"), dates[0] if dates else None)
        return self._render(request, doctor, BookingForm(doctor=doctor, day=day), day)

    def post(self, request, slug):
        doctor = self._get_doctor(slug)
        dates = available_dates(doctor, days=21)
        day = _parse_day(request.POST.get("date"), dates[0] if dates else None)
        form = BookingForm(request.POST, doctor=doctor, day=day)
        if form.is_valid():
            try:
                appointment = services.book_slot(
                    int(form.cleaned_data["slot"]),
                    actor=request.user,
                    reason=form.cleaned_data.get("reason", ""),
                    doctor=doctor,
                )
            except services.BookingError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request,
                    f"Appointment booked. Your reference is {appointment.reference}.",
                )
                return redirect(
                    "appointments:detail", reference=appointment.reference
                )
        else:
            messages.error(request, "Please choose an available slot.")
        return self._render(request, doctor, form, day)


class AppointmentListView(LoginRequiredMixin, ListView):
    template_name = "appointments/appointment_list.html"
    context_object_name = "appointments"

    def get_scope(self):
        return self.request.GET.get("scope", "upcoming")

    def get_queryset(self):
        qs = Appointment.objects.for_user(self.request.user).select_related(
            "doctor__user", "patient", "slot"
        )
        today = timezone.localdate()
        if self.get_scope() == "past":
            return qs.filter(date__lt=today).order_by("-date", "-start_time")
        return qs.filter(date__gte=today).order_by("date", "start_time")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["scope"] = self.get_scope()
        return context


class AppointmentDetailView(LoginRequiredMixin, DetailView):
    template_name = "appointments/appointment_detail.html"
    context_object_name = "appointment"
    slug_field = "reference"
    slug_url_kwarg = "reference"

    def get_queryset(self):
        return Appointment.objects.for_user(self.request.user).select_related(
            "doctor__user", "patient", "slot"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_cancel"] = services.can_cancel(self.object, self.request.user)
        context["can_reschedule"] = services.can_reschedule(
            self.object, self.request.user
        )
        return context


class CancelAppointmentView(LoginRequiredMixin, View):
    template_name = "appointments/appointment_cancel.html"

    def get(self, request, reference):
        appointment = _scoped_appointment(request, reference)
        if not services.can_cancel(appointment, request.user):
            raise PermissionDenied("This appointment cannot be cancelled by you.")
        return render(
            request,
            self.template_name,
            {"appointment": appointment, "form": CancelForm()},
        )

    def post(self, request, reference):
        appointment = _scoped_appointment(request, reference)
        if not services.can_cancel(appointment, request.user):
            raise PermissionDenied("This appointment cannot be cancelled by you.")
        form = CancelForm(request.POST)
        if form.is_valid():
            try:
                services.cancel_appointment(
                    appointment.pk,
                    actor=request.user,
                    reason=form.cleaned_data.get("reason", ""),
                )
            except services.BookingError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request, f"Appointment {appointment.reference} was cancelled."
                )
        return redirect("appointments:detail", reference=appointment.reference)


class RescheduleAppointmentView(LoginRequiredMixin, View):
    template_name = "appointments/appointment_reschedule.html"

    def _render(self, request, appointment, form, day):
        dates = available_dates(appointment.doctor, days=21)
        if day is None:
            day = dates[0] if dates else timezone.localdate()
        return render(
            request,
            self.template_name,
            {
                "appointment": appointment,
                "form": form,
                "dates": dates,
                "selected_day": day,
                "slots": available_slots(appointment.doctor, day),
            },
        )

    def get(self, request, reference):
        appointment = _scoped_appointment(request, reference)
        if not services.can_reschedule(appointment, request.user):
            raise PermissionDenied("This appointment cannot be rescheduled by you.")
        dates = available_dates(appointment.doctor, days=21)
        day = _parse_day(request.GET.get("date"), dates[0] if dates else None)
        return self._render(
            request,
            appointment,
            RescheduleForm(doctor=appointment.doctor, day=day),
            day,
        )

    def post(self, request, reference):
        appointment = _scoped_appointment(request, reference)
        if not services.can_reschedule(appointment, request.user):
            raise PermissionDenied("This appointment cannot be rescheduled by you.")
        dates = available_dates(appointment.doctor, days=21)
        day = _parse_day(request.POST.get("date"), dates[0] if dates else None)
        form = RescheduleForm(request.POST, doctor=appointment.doctor, day=day)
        if form.is_valid():
            try:
                services.reschedule_appointment(
                    appointment.pk,
                    actor=request.user,
                    new_slot_id=int(form.cleaned_data["slot"]),
                )
            except services.BookingError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Appointment rescheduled.")
                return redirect(
                    "appointments:detail", reference=appointment.reference
                )
        else:
            messages.error(request, "Please choose an available slot.")
        return self._render(request, appointment, form, day)
