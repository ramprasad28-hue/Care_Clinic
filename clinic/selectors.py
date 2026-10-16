"""Scoped read helpers for the clinic app.

These functions centralise the "what is publicly visible" and "what does this
doctor own" questions so views never hand-roll filtering. Public pages use the
``public``/``active`` scopes; doctor self-service uses the ownership scopes.
"""
from .models import AvailabilityRule, Doctor, DoctorLeave, Speciality


def active_specialities():
    return Speciality.objects.active()


def public_doctors(speciality_slug=None):
    qs = Doctor.objects.public()
    if speciality_slug:
        qs = qs.filter(speciality__slug=speciality_slug)
    return qs


def doctor_availability(doctor):
    return AvailabilityRule.objects.filter(doctor=doctor).order_by("weekday", "start_time")


def doctor_leaves(doctor):
    return DoctorLeave.objects.filter(doctor=doctor).order_by("-start_date")
