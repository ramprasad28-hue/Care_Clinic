"""Appointment domain models: concrete bookable slots and appointments.

Design notes (see ``docs/decisions.md`` ADR-016/ADR-017/ADR-018):

* **Concrete slots.** ``AppointmentSlot`` rows are materialized from
  ``clinic.AvailabilityRule`` windows by :mod:`appointments.slot_generation`.
  A slot has a lifecycle status (``OPEN``/``BOOKED``/``BLOCKED``).
* **One active booking per slot, enforced by the database.** ``Appointment.slot``
  is a *nullable* ``OneToOneField``. A cancelled/rescheduled appointment releases
  its slot back to ``OPEN`` and sets ``slot = NULL``; therefore the underlying
  unique index only ever covers the single *active* appointment for a slot. This
  gives a hard, portable DB guarantee (MySQL, SQLite, PostgreSQL) rather than the
  MySQL-unsupported *conditional* unique constraint described in the data model.
* **History is preserved.** Cancelling never deletes an appointment; it records
  the actor/reason and keeps the date/time snapshots.
* **Role validation.** ``clean()`` asserts the patient is a PATIENT and the
  doctor's user is a DOCTOR.
"""
import uuid
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.models import User
from clinic.models import Doctor

Role = User.Role


class SlotStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    BOOKED = "BOOKED", _("Booked")
    BLOCKED = "BLOCKED", _("Blocked")


class AppointmentStatus(models.TextChoices):
    REQUESTED = "REQUESTED", _("Requested")
    CONFIRMED = "CONFIRMED", _("Confirmed")
    CHECKED_IN = "CHECKED_IN", _("Checked in")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")
    NO_SHOW = "NO_SHOW", _("No show")


#: Statuses that make a slot "taken" (an appointment that is not finished).
ACTIVE_STATUSES = (
    AppointmentStatus.REQUESTED,
    AppointmentStatus.CONFIRMED,
    AppointmentStatus.CHECKED_IN,
)

#: Terminal statuses; no further transitions are permitted.
TERMINAL_STATUSES = (
    AppointmentStatus.COMPLETED,
    AppointmentStatus.CANCELLED,
    AppointmentStatus.NO_SHOW,
)

#: State machine: current status -> set of statuses it may move to.
ALLOWED_TRANSITIONS = {
    AppointmentStatus.REQUESTED: {AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED},
    AppointmentStatus.CONFIRMED: {
        AppointmentStatus.CHECKED_IN,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.CHECKED_IN: {AppointmentStatus.COMPLETED},
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.NO_SHOW: set(),
}

#: Free self-service cancellation/reschedule window (Q3 provisional).
CANCELLATION_WINDOW = timedelta(hours=24)


def _aware(day, time_value):
    """Combine a date and a time into a timezone-aware datetime in ``TIME_ZONE``."""
    return timezone.make_aware(
        datetime.combine(day, time_value), timezone.get_current_timezone()
    )


class AppointmentSlotQuerySet(models.QuerySet):
    def open(self):
        return self.filter(status=SlotStatus.OPEN)

    def for_doctor(self, doctor):
        return self.filter(doctor=doctor)

    def in_range(self, start, end):
        return self.filter(date__range=(start, end))


class AppointmentSlot(models.Model):
    """A concrete interval a patient can book (materialized from availability)."""

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="slots",
        verbose_name=_("doctor"),
    )
    date = models.DateField(_("date"))
    start_time = models.TimeField(_("start time"))
    end_time = models.TimeField(_("end time"))
    status = models.CharField(
        _("status"),
        max_length=10,
        choices=SlotStatus.choices,
        default=SlotStatus.OPEN,
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    objects = AppointmentSlotQuerySet.as_manager()

    class Meta:
        verbose_name = _("appointment slot")
        verbose_name_plural = _("appointment slots")
        ordering = ["date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "start_time"],
                name="appt_slot_unique_doctor_date_start",
            ),
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="appt_slot_end_after_start",
            ),
        ]
        indexes = [
            models.Index(
                fields=["doctor", "date", "status"],
                name="appt_slot_doc_date_status_idx",
            ),
            models.Index(fields=["date", "status"], name="appt_slot_date_status_idx"),
        ]

    def __str__(self):
        return f"{self.doctor} {self.date} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

    @property
    def start_datetime(self):
        return _aware(self.date, self.start_time)

    @property
    def end_datetime(self):
        return _aware(self.date, self.end_time)

    @property
    def is_past(self):
        return self.end_datetime <= timezone.now()

    @property
    def is_open(self):
        return self.status == SlotStatus.OPEN


class AppointmentQuerySet(models.QuerySet):
    def active(self):
        return self.filter(status__in=ACTIVE_STATUSES)

    def for_user(self, user):
        """Return only the appointments ``user`` is allowed to see.

        * Patients: their own appointments.
        * Doctors: appointments on their own schedule.
        * Receptionists / Administrators / superusers: everything.

        This is the single source of truth for record ownership; object lookups
        must always go *through* this queryset so an unauthorized id yields 404.
        """
        if not getattr(user, "is_authenticated", False):
            return self.none()
        role = getattr(user, "role", None)
        if user.is_superuser or role in (Role.ADMIN, Role.RECEPTIONIST):
            return self
        if role == Role.DOCTOR:
            return self.filter(doctor__user=user)
        if role == Role.PATIENT:
            return self.filter(patient=user)
        return self.none()


class Appointment(models.Model):
    """A booking made by (or on behalf of) a patient for a concrete slot."""

    reference = models.CharField(
        _("reference"), max_length=20, unique=True, db_index=True, blank=True
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name=_("patient"),
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.PROTECT,
        related_name="appointments",
        verbose_name=_("doctor"),
    )
    # Nullable so a cancelled/rescheduled booking can release the slot while the
    # appointment row (and its history) is preserved. The unique index on the
    # non-null values is what guarantees one *active* booking per slot.
    slot = models.OneToOneField(
        AppointmentSlot,
        on_delete=models.PROTECT,
        related_name="appointment",
        null=True,
        blank=True,
        verbose_name=_("slot"),
    )
    date = models.DateField(_("date"))
    start_time = models.TimeField(_("start time"))
    end_time = models.TimeField(_("end time"))
    status = models.CharField(
        _("status"),
        max_length=12,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.REQUESTED,
    )
    reason = models.CharField(_("reason"), max_length=255, blank=True)
    booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="appointments_booked",
        null=True,
        blank=True,
        verbose_name=_("booked by"),
    )
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="appointments_cancelled",
        null=True,
        blank=True,
        verbose_name=_("cancelled by"),
    )
    cancellation_reason = models.CharField(
        _("cancellation reason"), max_length=255, blank=True
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    objects = AppointmentQuerySet.as_manager()

    class Meta:
        verbose_name = _("appointment")
        verbose_name_plural = _("appointments")
        ordering = ["-date", "-start_time", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="appt_end_after_start",
            ),
        ]
        indexes = [
            models.Index(fields=["doctor", "date"], name="appt_doctor_date_idx"),
            models.Index(fields=["patient", "date"], name="appt_patient_date_idx"),
            models.Index(fields=["status"], name="appt_status_idx"),
        ]

    def __str__(self):
        return f"{self.reference} ({self.get_status_display()})"

    # --- Datetime helpers -------------------------------------------------
    @property
    def start_datetime(self):
        return _aware(self.date, self.start_time)

    @property
    def end_datetime(self):
        return _aware(self.date, self.end_time)

    @property
    def is_active_status(self):
        return self.status in ACTIVE_STATUSES

    @property
    def is_terminal(self):
        return self.status in TERMINAL_STATUSES

    @property
    def is_cancellable(self):
        return self.is_active_status

    def can_transition_to(self, new_status):
        return new_status in ALLOWED_TRANSITIONS.get(self.status, set())

    def within_self_service_window(self, now=None):
        """True if *now* is still within the free cancellation window."""
        now = now or timezone.now()
        return now <= self.start_datetime - CANCELLATION_WINDOW

    # --- Validation & persistence ----------------------------------------
    def clean(self):
        super().clean()
        errors = {}
        if self.patient_id and self.patient.role != Role.PATIENT:
            errors["patient"] = _("The patient must have the PATIENT role.")
        if self.doctor_id and self.doctor.user.role != Role.DOCTOR:
            errors["doctor"] = _("The linked user must have the DOCTOR role.")
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            errors["end_time"] = _("End time must be later than start time.")
        if errors:
            raise ValidationError(errors)

    def _build_reference(self):
        return f"CC-{timezone.now().year}-{self.pk:06d}"

    def save(self, *args, **kwargs):
        if self.reference:
            self.full_clean()
            super().save(*args, **kwargs)
            return
        # First insert: use a unique temporary reference, obtain the PK, then
        # replace it with the final PK-derived reference (race-free because the
        # PK is unique).
        self.reference = f"TMP-{uuid.uuid4().hex[:12]}"
        self.full_clean()
        super().save(*args, **kwargs)
        self.reference = self._build_reference()
        super().save(update_fields=["reference"])

    def get_absolute_url(self):
        return reverse("appointments:detail", kwargs={"reference": self.reference})
