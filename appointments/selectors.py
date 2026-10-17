"""Scoped read helpers for appointments.

Views must never hand-roll these queries. Public/booking slot lookups use the
``available_*`` helpers; appointment record access always goes through
``Appointment.objects.for_user`` (see :mod:`appointments.models`).
"""
from datetime import timedelta

from django.utils import timezone

from clinic.models import DoctorLeave

from .models import Appointment, AppointmentSlot, SlotStatus


def doctor_on_leave(doctor, day):
    """True if ``doctor`` has an (inclusive) leave range covering ``day``."""
    return DoctorLeave.objects.filter(
        doctor=doctor, start_date__lte=day, end_date__gte=day
    ).exists()


def available_slots(doctor, day, *, now=None):
    """Open, future, non-leave slots for ``doctor`` on ``day`` (ordered)."""
    now = now or timezone.now()
    if doctor_on_leave(doctor, day):
        return AppointmentSlot.objects.none()
    slots = AppointmentSlot.objects.filter(
        doctor=doctor, date=day, status=SlotStatus.OPEN
    ).order_by("start_time")
    # Exclude slots that have already started.
    ids = [slot.pk for slot in slots if slot.start_datetime > now]
    return AppointmentSlot.objects.filter(pk__in=ids).order_by("start_time")


def available_dates(doctor, days=21, *, now=None):
    """Dates (ascending) within the next ``days`` that have at least one slot."""
    now = now or timezone.now()
    today = timezone.localdate(now)
    horizon = today + timedelta(days=days)
    slots = AppointmentSlot.objects.filter(
        doctor=doctor,
        status=SlotStatus.OPEN,
        date__gte=today,
        date__lte=horizon,
    ).order_by("date", "start_time")
    # Expand leave ranges into individual dates (cheap for a small horizon).
    leave_dates = set()
    for leave in DoctorLeave.objects.filter(
        doctor=doctor, end_date__gte=today, start_date__lte=horizon
    ).only("start_date", "end_date"):
        d = max(leave.start_date, today)
        while d <= min(leave.end_date, horizon):
            leave_dates.add(d)
            d += timedelta(days=1)

    seen = []
    for slot in slots:
        if slot.date in leave_dates:
            continue
        if slot.start_datetime <= now:
            continue
        if slot.date not in seen:
            seen.append(slot.date)
    return seen


def appointments_for(user):
    return Appointment.objects.for_user(user)
