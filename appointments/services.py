"""Transactional booking services.

All booking mutations flow through this module. Each operation runs inside
``transaction.atomic()`` and locks the relevant ``AppointmentSlot`` row with
``select_for_update()`` (a no-op on SQLite, real row locks on MySQL/InnoDB —
see the MySQL validation procedure in ``docs/mysql-validation.md``).

Defense layers against double booking:

1. Application checks inside the transaction (friendly errors).
2. ``SELECT ... FOR UPDATE`` on the slot row (serializes concurrent claims).
3. Database uniqueness on ``Appointment.slot`` (one active booking per slot),
   surfaced as :class:`SlotUnavailable` when ``IntegrityError`` is raised.

Nothing here trusts a submitted patient/doctor id or role: the actor's role is
read from the session user and the patient is resolved/validated explicitly.
"""
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import (
    Appointment,
    AppointmentSlot,
    AppointmentStatus,
    Role,
    SlotStatus,
)
from .selectors import doctor_on_leave


class BookingError(Exception):
    """A user-facing business error (bad request, not a server fault)."""


class SlotUnavailable(BookingError):
    """The requested slot cannot be booked (gone, taken, or blocked)."""


class InvalidTransition(BookingError):
    """The requested appointment status transition is not permitted."""


# --------------------------------------------------------------------------
# Permission predicates (also used by views/templates and tests)
# --------------------------------------------------------------------------
def _is_staff_role(user):
    return bool(
        getattr(user, "is_authenticated", False)
        and (
            user.is_superuser
            or getattr(user, "role", None) in (Role.RECEPTIONIST, Role.ADMIN)
        )
    )


def can_book_for(actor, patient):
    if not getattr(actor, "is_authenticated", False):
        return False
    if _is_staff_role(actor):
        return patient is not None and getattr(patient, "role", None) == Role.PATIENT
    if getattr(actor, "role", None) == Role.PATIENT:
        return patient is not None and patient.pk == actor.pk
    return False


def can_cancel(appointment, actor):
    if not getattr(actor, "is_authenticated", False) or not appointment.is_active_status:
        return False
    if _is_staff_role(actor):
        return True
    if getattr(actor, "role", None) == Role.PATIENT and appointment.patient_id == actor.pk:
        return appointment.within_self_service_window()
    return False


def can_reschedule(appointment, actor):
    reschedulable = appointment.status in (
        AppointmentStatus.REQUESTED,
        AppointmentStatus.CONFIRMED,
    )
    if not getattr(actor, "is_authenticated", False) or not reschedulable:
        return False
    if _is_staff_role(actor):
        return True
    if getattr(actor, "role", None) == Role.PATIENT and appointment.patient_id == actor.pk:
        return appointment.within_self_service_window()
    return False


def can_update_status(appointment, actor):
    if not getattr(actor, "is_authenticated", False):
        return False
    if _is_staff_role(actor):
        return True
    if getattr(actor, "role", None) == Role.DOCTOR:
        return getattr(actor, "doctor", None) is not None and (
            appointment.doctor_id == actor.doctor.pk
        )
    return False


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _resolve_patient(actor, patient):
    if not getattr(actor, "is_authenticated", False):
        raise PermissionDenied("Authentication is required.")
    if _is_staff_role(actor):
        if patient is None:
            raise BookingError("A patient must be selected.")
        if patient.role != Role.PATIENT:
            raise BookingError("Appointments can only be booked for patients.")
        return patient
    if getattr(actor, "role", None) == Role.PATIENT:
        if patient is not None and patient.pk != actor.pk:
            raise PermissionDenied("You can only book appointments for yourself.")
        return actor
    raise PermissionDenied("Your role is not permitted to book appointments.")


def _lock_slot(slot_id):
    try:
        return (
            AppointmentSlot.objects.select_for_update()
            .select_related("doctor", "doctor__user")
            .get(pk=slot_id)
        )
    except AppointmentSlot.DoesNotExist:
        raise SlotUnavailable("That slot no longer exists.")


def _validate_slot_bookable(slot, *, now):
    if slot.status != SlotStatus.OPEN:
        raise SlotUnavailable("That slot is no longer available.")
    if slot.start_datetime <= now:
        raise BookingError("You cannot book a slot that has already started.")
    if doctor_on_leave(slot.doctor, slot.date):
        raise BookingError("The doctor is on leave on that date.")


# --------------------------------------------------------------------------
# Booking
# --------------------------------------------------------------------------
@transaction.atomic
def book_slot(slot_id, *, actor, patient=None, reason="", doctor=None):
    """Book ``slot_id`` for the resolved patient on behalf of ``actor``."""
    patient = _resolve_patient(actor, patient)
    slot = _lock_slot(slot_id)

    if doctor is not None and slot.doctor_id != doctor.pk:
        raise BookingError("That slot does not belong to the selected doctor.")
    if not slot.doctor.is_accepting_appointments:
        raise BookingError("This doctor is not accepting appointments.")

    now = timezone.now()
    _validate_slot_bookable(slot, now=now)

    slot.status = SlotStatus.BOOKED
    slot.save(update_fields=["status"])

    try:
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=slot.doctor,
            slot=slot,
            date=slot.date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            status=AppointmentStatus.REQUESTED,
            reason=(reason or "").strip()[:255],
            booked_by=actor,
        )
    except IntegrityError as exc:  # pragma: no cover - race on MySQL
        raise SlotUnavailable(
            "That slot was just booked by someone else. Please pick another."
        ) from exc
    return appointment


# --------------------------------------------------------------------------
# Cancellation
# --------------------------------------------------------------------------
@transaction.atomic
def cancel_appointment(appointment_pk, *, actor, reason=""):
    """Cancel an appointment, preserving the record and releasing the slot.

    The lookup goes through the role-scoped ``for_user`` queryset so a
    foreign (unauthorized) appointment is indistinguishable from a
    nonexistent one — only the actor's own record can ever be loaded here.
    """
    try:
        appointment = (
            Appointment.objects.for_user(actor)
            .select_for_update()
            .select_related("slot")
            .get(pk=appointment_pk)
        )
    except Appointment.DoesNotExist:
        raise BookingError("Appointment not found.")

    if not appointment.is_active_status:
        raise InvalidTransition("This appointment can no longer be cancelled.")
    if not can_cancel(appointment, actor):
        raise PermissionDenied("You are not allowed to cancel this appointment.")

    slot = appointment.slot

    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_by = actor
    appointment.cancellation_reason = (reason or "").strip()[:255]
    appointment.slot = None
    appointment.save(update_fields=[
        "status",
        "cancelled_by",
        "cancellation_reason",
        "slot",
        "updated_at",
    ])
    if slot is not None and slot.start_datetime > timezone.now():
        slot.status = SlotStatus.OPEN
        slot.save(update_fields=["status"])
    return appointment


# --------------------------------------------------------------------------
# Rescheduling
# --------------------------------------------------------------------------
@transaction.atomic
def reschedule_appointment(appointment_pk, *, actor, new_slot_id):
    """Move an active appointment to ``new_slot_id`` atomically.

    If anything fails the whole transaction rolls back, leaving the original
    booking intact. The lookup goes through the role-scoped ``for_user``
    queryset; a foreign (unauthorized) appointment is indistinguishable
    from a nonexistent one.
    """
    try:
        appointment = (
            Appointment.objects.for_user(actor)
            .select_for_update()
            .select_related("slot")
            .get(pk=appointment_pk)
        )
    except Appointment.DoesNotExist:
        raise BookingError("Appointment not found.")

    if not can_reschedule(appointment, actor):
        raise PermissionDenied("You are not allowed to reschedule this appointment.")
    if appointment.slot_id == int(new_slot_id):
        raise BookingError("The appointment is already on that slot.")

    new_slot = _lock_slot(new_slot_id)
    if new_slot.doctor_id != appointment.doctor_id:
        raise BookingError("You can only reschedule to another slot of the same doctor.")

    now = timezone.now()
    _validate_slot_bookable(new_slot, now=now)

    old_slot = appointment.slot
    new_slot.status = SlotStatus.BOOKED
    new_slot.save(update_fields=["status"])

    appointment.slot = new_slot
    appointment.date = new_slot.date
    appointment.start_time = new_slot.start_time
    appointment.end_time = new_slot.end_time
    try:
        appointment.save()
    except IntegrityError as exc:  # pragma: no cover - race on MySQL
        raise SlotUnavailable("That slot was just taken. Please pick another.") from exc

    if old_slot is not None and old_slot.pk != new_slot.pk:
        if old_slot.start_datetime > now:
            old_slot.status = SlotStatus.OPEN
            old_slot.save(update_fields=["status"])
    return appointment


# --------------------------------------------------------------------------
# Status transitions
# --------------------------------------------------------------------------
@transaction.atomic
def transition_status(appointment_pk, *, actor, new_status, reason=""):
    """Apply an allowed status transition (never bypasses the state machine).

    The lookup goes through the role-scoped ``for_user`` queryset; a foreign
    (unauthorized) appointment is indistinguishable from a nonexistent one.
    """
    try:
        appointment = (
            Appointment.objects.for_user(actor)
            .select_for_update()
            .select_related("slot")
            .get(pk=appointment_pk)
        )
    except Appointment.DoesNotExist:
        raise BookingError("Appointment not found.")

    if not can_update_status(appointment, actor):
        raise PermissionDenied("You are not allowed to change this appointment's status.")
    if new_status == AppointmentStatus.CANCELLED:
        raise BookingError("Use the cancellation flow to cancel an appointment.")
    if not appointment.can_transition_to(new_status):
        raise InvalidTransition(
            f"Cannot move an appointment from {appointment.get_status_display()} "
            f"to {dict(AppointmentStatus.choices).get(new_status, new_status)}."
        )

    appointment.status = new_status
    appointment.save(update_fields=["status", "updated_at"])
    return appointment
