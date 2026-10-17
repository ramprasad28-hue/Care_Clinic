"""Tests for the appointments app: slot generation, booking, cancellation,
rescheduling, status transitions, ownership scoping, and the HTTP flows.

Runnable via either:
    python manage.py test
    pytest

The concurrency test is skipped unless the active database is MySQL (real
``SELECT ... FOR UPDATE`` row locks). See ``docs/mysql-validation.md``.
"""
import threading
import unittest
from datetime import time, timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from appointments import services
from appointments.models import (
    Appointment,
    AppointmentSlot,
    AppointmentStatus,
    SlotStatus,
)
from appointments.selectors import available_dates, available_slots, doctor_on_leave
from appointments.slot_generation import (
    _rule_intervals,
    generate_slots,
    generate_slots_for_doctor,
)
from clinic.models import AvailabilityRule, Doctor, DoctorLeave, Speciality

User = get_user_model()
PASSWORD = "S3cret-pass!"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def make_user(email, role=User.Role.PATIENT, **kwargs):
    kwargs.setdefault("first_name", role.title())
    kwargs.setdefault("last_name", "User")
    return User.objects.create_user(email=email, password=PASSWORD, role=role, **kwargs)


def make_doctor(
    email="doc@example.com",
    *,
    speciality=None,
    slot_length_minutes=30,
    is_accepting=True,
    **kwargs,
):
    user = kwargs.pop("user", None) or make_user(email, role=User.Role.DOCTOR)
    speciality = speciality or Speciality.objects.create(name=f"Spec {email}")
    return Doctor.objects.create(
        user=user,
        speciality=speciality,
        registration_number=f"REG-{email}",
        qualification="MBBS",
        slot_length_minutes=slot_length_minutes,
        is_accepting_appointments=is_accepting,
        **kwargs,
    )


def make_rule(doctor, weekday, start, end, slot_length=None, is_active=True):
    return AvailabilityRule.objects.create(
        doctor=doctor,
        weekday=weekday,
        start_time=start,
        end_time=end,
        slot_length_minutes=slot_length,
        is_active=is_active,
    )


def make_slot(doctor, day, start=time(9, 0), end=time(9, 30), status=SlotStatus.OPEN):
    return AppointmentSlot.objects.create(
        doctor=doctor, date=day, start_time=start, end_time=end, status=status
    )


def future_day(days=7):
    return timezone.localdate() + timedelta(days=days)


def near_future_slot(doctor, hours=2):
    """A slot that starts in ``hours`` (still fully bookable) — used for the
    cancellation-window tests where "7 days out" would always be cancellable."""
    start = timezone.localtime(timezone.now() + timedelta(hours=hours))
    end = start + timedelta(minutes=15)
    return make_slot(doctor, start.date(), start.time(), end.time())


# --------------------------------------------------------------------------
# Slot generation
# --------------------------------------------------------------------------
class SlotGenerationTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor(slot_length_minutes=30)

    def test_uses_doctor_default_slot_length(self):
        day = future_day(7)
        make_rule(self.doctor, day.weekday(), time(9, 0), time(9, 30))
        summary = generate_slots_for_doctor(self.doctor, day, day)
        self.assertEqual(summary["created"], 1)
        slot = AppointmentSlot.objects.get(doctor=self.doctor)
        self.assertEqual((slot.start_time, slot.end_time), (time(9, 0), time(9, 30)))

    def test_rule_override_slot_length(self):
        day = future_day(7)
        make_rule(self.doctor, day.weekday(), time(9, 0), time(9, 30), slot_length=15)
        generate_slots_for_doctor(self.doctor, day, day)
        slots = list(
            AppointmentSlot.objects.filter(doctor=self.doctor).order_by("start_time")
        )
        self.assertEqual(len(slots), 2)
        self.assertEqual(slots[0].start_time, time(9, 0))
        self.assertEqual(slots[1].start_time, time(9, 15))

    def test_never_extends_past_rule_end(self):
        day = future_day(7)
        make_rule(self.doctor, day.weekday(), time(9, 0), time(9, 40))
        generate_slots_for_doctor(self.doctor, day, day)
        slots = list(AppointmentSlot.objects.filter(doctor=self.doctor))
        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0].end_time, time(9, 30))

    def test_invalid_rule_yields_nothing(self):
        day = future_day(7)
        fake = SimpleNamespace(
            effective_slot_length_minutes=30,
            start_time=time(10, 0),
            end_time=time(9, 0),
        )
        self.assertEqual(list(_rule_intervals(fake, day)), [])

    def test_excludes_leave_dates(self):
        day = future_day(7)
        make_rule(self.doctor, day.weekday(), time(9, 0), time(10, 0))
        DoctorLeave.objects.create(
            doctor=self.doctor, start_date=day, end_date=day, reason="Conference"
        )
        summary = generate_slots_for_doctor(self.doctor, day, day)
        self.assertEqual(summary["created"], 0)
        self.assertTrue(doctor_on_leave(self.doctor, day))

    def test_excludes_past_unless_requested(self):
        past = timezone.localdate() - timedelta(days=3)
        make_rule(self.doctor, past.weekday(), time(9, 0), time(10, 0))
        self.assertEqual(
            generate_slots_for_doctor(self.doctor, past, past)["created"], 0
        )
        self.assertGreater(
            generate_slots_for_doctor(self.doctor, past, past, include_past=True)[
                "created"
            ],
            0,
        )

    def test_idempotent_across_runs(self):
        day = future_day(7)
        make_rule(self.doctor, day.weekday(), time(9, 0), time(10, 0))
        first = generate_slots_for_doctor(self.doctor, day, day)
        second = generate_slots_for_doctor(self.doctor, day, day)
        self.assertEqual(second["created"], 0)
        self.assertEqual(second["existing"], first["created"])
        self.assertEqual(AppointmentSlot.objects.filter(doctor=self.doctor).count(), first["created"])

    def test_regeneration_preserves_booked_slots(self):
        day = future_day(7)
        make_rule(self.doctor, day.weekday(), time(9, 0), time(10, 0))
        generate_slots_for_doctor(self.doctor, day, day)
        slot = AppointmentSlot.objects.filter(doctor=self.doctor).first()
        patient = make_user("p@example.com")
        services.book_slot(slot.pk, actor=patient)
        before = AppointmentSlot.objects.filter(doctor=self.doctor).count()
        summary = generate_slots_for_doctor(self.doctor, day, day)
        self.assertEqual(summary["created"], 0)
        self.assertEqual(AppointmentSlot.objects.filter(doctor=self.doctor).count(), before)
        self.assertEqual(
            AppointmentSlot.objects.get(pk=slot.pk).status, SlotStatus.BOOKED
        )

    def test_generate_slots_command(self):
        day = future_day(7)
        make_rule(self.doctor, day.weekday(), time(9, 0), time(10, 0))
        call_command(
            "generate_slots",
            start=day.isoformat(),
            end=day.isoformat(),
        )
        self.assertEqual(AppointmentSlot.objects.filter(doctor=self.doctor).count(), 2)

    def test_generate_slots_for_multiple_doctors(self):
        other = make_doctor("doc2@example.com", speciality=self.doctor.speciality)
        day = future_day(7)
        make_rule(self.doctor, day.weekday(), time(9, 0), time(10, 0))
        make_rule(other, day.weekday(), time(9, 0), time(10, 0))
        summary = generate_slots(
            day, day, doctors=[self.doctor, other], now=timezone.now()
        )
        self.assertEqual(set(summary.keys()), {self.doctor.pk, other.pk})


# --------------------------------------------------------------------------
# Slot model & selectors
# --------------------------------------------------------------------------
class SlotModelTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()

    def test_unique_doctor_date_start(self):
        day = future_day(3)
        make_slot(self.doctor, day, time(9, 0), time(9, 30))
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_slot(self.doctor, day, time(9, 0), time(9, 45))

    def test_end_after_start_constraint(self):
        day = future_day(3)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                make_slot(self.doctor, day, time(9, 30), time(9, 0))

    def test_is_past_and_is_open(self):
        past = timezone.localdate() - timedelta(days=1)
        past_slot = make_slot(self.doctor, past)
        self.assertTrue(past_slot.is_past)
        self.assertTrue(past_slot.is_open)
        future_slot = make_slot(self.doctor, future_day(3))
        self.assertFalse(future_slot.is_past)


class AvailableSelectorTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()

    def test_available_slots_excludes_past_booked_and_blocked(self):
        day = future_day(5)
        open_slot = make_slot(self.doctor, day, time(9, 0), time(9, 30))
        make_slot(self.doctor, day, time(9, 30), time(10, 0), status=SlotStatus.BOOKED)
        make_slot(self.doctor, day, time(10, 0), time(10, 30), status=SlotStatus.BLOCKED)
        past = make_slot(self.doctor, timezone.localdate() - timedelta(days=1))
        result = list(available_slots(self.doctor, day))
        self.assertEqual(result, [open_slot])
        self.assertNotIn(past, available_slots(self.doctor, timezone.localdate() - timedelta(days=1)))

    def test_available_dates_ascending_and_skips_leave(self):
        d1 = future_day(5)
        d2 = future_day(6)
        make_slot(self.doctor, d1, time(9, 0), time(9, 30))
        make_slot(self.doctor, d1, time(9, 30), time(10, 0))
        make_slot(self.doctor, d2, time(9, 0), time(9, 30))
        DoctorLeave.objects.create(doctor=self.doctor, start_date=d2, end_date=d2)
        dates = available_dates(self.doctor, days=21)
        self.assertEqual(dates, [d1])

    def test_available_dates_respects_horizon(self):
        far = future_day(40)
        make_slot(self.doctor, far, time(9, 0), time(9, 30))
        self.assertEqual(available_dates(self.doctor, days=21), [])


# --------------------------------------------------------------------------
# Booking service
# --------------------------------------------------------------------------
class BookingServiceTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()
        self.patient = make_user("patient@example.com")

    def test_book_slot_success(self):
        slot = make_slot(self.doctor, future_day(5))
        appointment = services.book_slot(slot.pk, actor=self.patient, reason="Checkup")
        self.assertEqual(appointment.status, AppointmentStatus.REQUESTED)
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.booked_by, self.patient)
        self.assertEqual(appointment.reason, "Checkup")
        self.assertEqual(appointment.reference[:3], "CC-")
        slot.refresh_from_db()
        self.assertEqual(slot.status, SlotStatus.BOOKED)

    def test_reference_format_and_uniqueness(self):
        slot1 = make_slot(self.doctor, future_day(5), time(9, 0), time(9, 30))
        slot2 = make_slot(self.doctor, future_day(5), time(9, 30), time(10, 0))
        a1 = services.book_slot(slot1.pk, actor=self.patient)
        a2 = services.book_slot(slot2.pk, actor=self.patient)
        year = timezone.now().year
        self.assertEqual(a1.reference, f"CC-{year}-{a1.pk:06d}")
        self.assertNotEqual(a1.reference, a2.reference)
        # Saving again must not regenerate the reference.
        a1.reason = "updated"
        a1.save()
        self.assertEqual(a1.reference, f"CC-{year}-{a1.pk:06d}")

    def test_double_booking_blocked(self):
        slot = make_slot(self.doctor, future_day(5))
        services.book_slot(slot.pk, actor=self.patient)
        other = make_user("other@example.com")
        with self.assertRaises(services.SlotUnavailable):
            services.book_slot(slot.pk, actor=other)

    def test_cannot_book_blocked_slot(self):
        slot = make_slot(self.doctor, future_day(5), status=SlotStatus.BLOCKED)
        with self.assertRaises(services.SlotUnavailable):
            services.book_slot(slot.pk, actor=self.patient)

    def test_cannot_book_past_slot(self):
        slot = make_slot(self.doctor, timezone.localdate() - timedelta(days=1))
        with self.assertRaises(services.BookingError):
            services.book_slot(slot.pk, actor=self.patient)

    def test_cannot_book_during_leave(self):
        day = future_day(5)
        slot = make_slot(self.doctor, day)
        DoctorLeave.objects.create(doctor=self.doctor, start_date=day, end_date=day)
        with self.assertRaises(services.BookingError):
            services.book_slot(slot.pk, actor=self.patient)

    def test_cannot_book_for_inactive_doctor(self):
        doctor = make_doctor("inactive@example.com", is_accepting=False,
                             speciality=self.doctor.speciality)
        slot = make_slot(doctor, future_day(5))
        with self.assertRaises(services.BookingError):
            services.book_slot(slot.pk, actor=self.patient)

    def test_patient_cannot_book_for_someone_else(self):
        other = make_user("other@example.com")
        slot = make_slot(self.doctor, future_day(5))
        with self.assertRaises(PermissionDenied):
            services.book_slot(slot.pk, actor=self.patient, patient=other)

    def test_doctor_cannot_book(self):
        doctor_actor = self.doctor.user
        slot = make_slot(self.doctor, future_day(5))
        with self.assertRaises(PermissionDenied):
            services.book_slot(slot.pk, actor=doctor_actor)

    def test_missing_slot_raises(self):
        with self.assertRaises(services.SlotUnavailable):
            services.book_slot(999999, actor=self.patient)

    def test_receptionist_books_for_patient(self):
        receptionist = make_user("recep@example.com", role=User.Role.RECEPTIONIST)
        slot = make_slot(self.doctor, future_day(5))
        appointment = services.book_slot(
            slot.pk, actor=receptionist, patient=self.patient
        )
        self.assertEqual(appointment.patient, self.patient)
        self.assertEqual(appointment.booked_by, receptionist)

    def test_receptionist_cannot_book_for_non_patient(self):
        receptionist = make_user("recep2@example.com", role=User.Role.RECEPTIONIST)
        slot = make_slot(self.doctor, future_day(5))
        with self.assertRaises(services.BookingError):
            services.book_slot(slot.pk, actor=receptionist, patient=self.doctor.user)

    def test_booking_wrong_doctor_slot_rejected(self):
        other = make_doctor("doc2@example.com", speciality=self.doctor.speciality)
        slot = make_slot(other, future_day(5))
        with self.assertRaises(services.BookingError):
            services.book_slot(slot.pk, actor=self.patient, doctor=self.doctor)


# --------------------------------------------------------------------------
# Ownership scoping (for_user)
# --------------------------------------------------------------------------
class OwnershipScopingTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()
        self.patient_a = make_user("a@example.com")
        self.patient_b = make_user("b@example.com")
        slot_a = make_slot(self.doctor, future_day(5), time(9, 0), time(9, 30))
        slot_b = make_slot(self.doctor, future_day(5), time(9, 30), time(10, 0))
        self.appt_a = services.book_slot(slot_a.pk, actor=self.patient_a)
        self.appt_b = services.book_slot(slot_b.pk, actor=self.patient_b)

    def test_patient_sees_only_own(self):
        refs = set(Appointment.objects.for_user(self.patient_a).values_list("reference", flat=True))
        self.assertEqual(refs, {self.appt_a.reference})

    def test_doctor_sees_schedule(self):
        refs = set(Appointment.objects.for_user(self.doctor.user).values_list("reference", flat=True))
        self.assertEqual(refs, {self.appt_a.reference, self.appt_b.reference})

    def test_other_doctor_sees_none(self):
        other = make_doctor("other@example.com", speciality=self.doctor.speciality)
        self.assertEqual(Appointment.objects.for_user(other.user).count(), 0)

    def test_receptionist_and_admin_see_all(self):
        for role in (User.Role.RECEPTIONIST, User.Role.ADMIN):
            user = make_user(f"{role.lower()}@example.com", role=role)
            self.assertEqual(Appointment.objects.for_user(user).count(), 2)


# --------------------------------------------------------------------------
# Cancellation
# --------------------------------------------------------------------------
class CancellationTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()
        self.patient = make_user("patient@example.com")
        self.receptionist = make_user("recep@example.com", role=User.Role.RECEPTIONIST)

    def test_cancel_releases_slot_and_keeps_history(self):
        day = future_day(5)
        slot = make_slot(self.doctor, day)
        appointment = services.book_slot(slot.pk, actor=self.patient)
        services.cancel_appointment(appointment.pk, actor=self.patient, reason="Sick")
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, AppointmentStatus.CANCELLED)
        self.assertIsNone(appointment.slot)
        self.assertEqual(appointment.cancelled_by, self.patient)
        self.assertEqual(appointment.cancellation_reason, "Sick")
        # Date snapshots preserved.
        self.assertEqual(appointment.date, day)
        slot.refresh_from_db()
        self.assertEqual(slot.status, SlotStatus.OPEN)

    def test_released_slot_can_be_rebooked(self):
        slot = make_slot(self.doctor, future_day(5))
        appointment = services.book_slot(slot.pk, actor=self.patient)
        services.cancel_appointment(appointment.pk, actor=self.patient)
        other = make_user("other@example.com")
        rebooked = services.book_slot(slot.pk, actor=other)
        self.assertEqual(rebooked.patient, other)

    def test_self_cancel_blocked_inside_window(self):
        slot = near_future_slot(self.doctor, hours=2)
        appointment = services.book_slot(slot.pk, actor=self.patient)
        self.assertFalse(services.can_cancel(appointment, self.patient))
        with self.assertRaises(PermissionDenied):
            services.cancel_appointment(appointment.pk, actor=self.patient)

    def test_staff_can_cancel_inside_window(self):
        slot = near_future_slot(self.doctor, hours=2)
        appointment = services.book_slot(slot.pk, actor=self.patient)
        self.assertTrue(services.can_cancel(appointment, self.receptionist))
        services.cancel_appointment(appointment.pk, actor=self.receptionist)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, AppointmentStatus.CANCELLED)

    def test_other_patient_cannot_cancel(self):
        slot = make_slot(self.doctor, future_day(5))
        appointment = services.book_slot(slot.pk, actor=self.patient)
        other = make_user("other@example.com")
        with self.assertRaises(PermissionDenied):
            services.cancel_appointment(appointment.pk, actor=other)

    def test_cannot_cancel_twice(self):
        slot = make_slot(self.doctor, future_day(5))
        appointment = services.book_slot(slot.pk, actor=self.patient)
        services.cancel_appointment(appointment.pk, actor=self.patient)
        with self.assertRaises(services.BookingError):
            services.cancel_appointment(appointment.pk, actor=self.patient)


# --------------------------------------------------------------------------
# Rescheduling
# --------------------------------------------------------------------------
class ReschedulingTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()
        self.patient = make_user("patient@example.com")
        self.slot_a = make_slot(self.doctor, future_day(5), time(9, 0), time(9, 30))
        self.slot_b = make_slot(self.doctor, future_day(5), time(9, 30), time(10, 0))
        self.appointment = services.book_slot(self.slot_a.pk, actor=self.patient)

    def test_reschedule_moves_and_frees_old_slot(self):
        services.reschedule_appointment(
            self.appointment.pk, actor=self.patient, new_slot_id=self.slot_b.pk
        )
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.slot, self.slot_b)
        self.assertEqual(self.appointment.start_time, time(9, 30))
        self.slot_a.refresh_from_db()
        self.slot_b.refresh_from_db()
        self.assertEqual(self.slot_a.status, SlotStatus.OPEN)
        self.assertEqual(self.slot_b.status, SlotStatus.BOOKED)

    def test_cannot_reschedule_to_same_slot(self):
        with self.assertRaises(services.BookingError):
            services.reschedule_appointment(
                self.appointment.pk, actor=self.patient, new_slot_id=self.slot_a.pk
            )

    def test_cannot_reschedule_to_taken_slot(self):
        other = make_user("other@example.com")
        services.book_slot(self.slot_b.pk, actor=other)
        with self.assertRaises(services.SlotUnavailable):
            services.reschedule_appointment(
                self.appointment.pk, actor=self.patient, new_slot_id=self.slot_b.pk
            )

    def test_cannot_reschedule_to_another_doctor(self):
        other = make_doctor("doc2@example.com", speciality=self.doctor.speciality)
        foreign = make_slot(other, future_day(5), time(11, 0), time(11, 30))
        with self.assertRaises(services.BookingError):
            services.reschedule_appointment(
                self.appointment.pk, actor=self.patient, new_slot_id=foreign.pk
            )

    def test_other_patient_cannot_reschedule(self):
        other = make_user("other@example.com")
        with self.assertRaises(PermissionDenied):
            services.reschedule_appointment(
                self.appointment.pk, actor=other, new_slot_id=self.slot_b.pk
            )


# --------------------------------------------------------------------------
# Status transitions
# --------------------------------------------------------------------------
class StatusTransitionTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()
        self.patient = make_user("patient@example.com")
        self.admin = make_user("admin@example.com", role=User.Role.ADMIN)
        slot = make_slot(self.doctor, future_day(5))
        self.appointment = services.book_slot(slot.pk, actor=self.patient)

    def test_valid_transition_chain(self):
        services.transition_status(
            self.appointment.pk, actor=self.admin, new_status=AppointmentStatus.CONFIRMED
        )
        services.transition_status(
            self.appointment.pk, actor=self.admin, new_status=AppointmentStatus.CHECKED_IN
        )
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, AppointmentStatus.CHECKED_IN)
        services.transition_status(
            self.appointment.pk, actor=self.admin, new_status=AppointmentStatus.COMPLETED
        )
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, AppointmentStatus.COMPLETED)

    def test_invalid_transition_rejected(self):
        with self.assertRaises(services.InvalidTransition):
            services.transition_status(
                self.appointment.pk,
                actor=self.admin,
                new_status=AppointmentStatus.COMPLETED,
            )

    def test_terminal_status_has_no_transitions(self):
        services.cancel_appointment(self.appointment.pk, actor=self.admin)
        self.appointment.refresh_from_db()
        self.assertTrue(self.appointment.is_terminal)
        with self.assertRaises(services.BookingError):
            services.transition_status(
                self.appointment.pk,
                actor=self.admin,
                new_status=AppointmentStatus.CONFIRMED,
            )

    def test_cancel_via_transition_rejected(self):
        with self.assertRaises(services.BookingError):
            services.transition_status(
                self.appointment.pk,
                actor=self.admin,
                new_status=AppointmentStatus.CANCELLED,
            )

    def test_doctor_can_update_own_appointment(self):
        services.transition_status(
            self.appointment.pk,
            actor=self.doctor.user,
            new_status=AppointmentStatus.CONFIRMED,
        )
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, AppointmentStatus.CONFIRMED)

    def test_doctor_cannot_update_others_appointment(self):
        other_doctor = make_doctor("doc2@example.com", speciality=self.doctor.speciality)
        with self.assertRaises(PermissionDenied):
            services.transition_status(
                self.appointment.pk,
                actor=other_doctor.user,
                new_status=AppointmentStatus.CONFIRMED,
            )

    def test_patient_cannot_update_status(self):
        with self.assertRaises(PermissionDenied):
            services.transition_status(
                self.appointment.pk,
                actor=self.patient,
                new_status=AppointmentStatus.CONFIRMED,
            )

    def test_can_transition_to_helper(self):
        self.assertTrue(self.appointment.can_transition_to(AppointmentStatus.CONFIRMED))
        self.assertFalse(self.appointment.can_transition_to(AppointmentStatus.COMPLETED))


# --------------------------------------------------------------------------
# HTTP views
# --------------------------------------------------------------------------
class BookingViewTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()
        self.patient = make_user("patient@example.com")
        self.slot = make_slot(self.doctor, future_day(5), time(9, 0), time(9, 30))
        self.client = Client()

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("appointments:book", args=[self.doctor.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_wrong_role_forbidden(self):
        self.client.force_login(self.doctor.user)
        response = self.client.get(reverse("appointments:book", args=[self.doctor.slug]))
        self.assertEqual(response.status_code, 403)

    def test_patient_can_view_booking_page(self):
        self.client.force_login(self.patient)
        response = self.client.get(reverse("appointments:book", args=[self.doctor.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.doctor.user.get_full_name())

    def test_patient_can_book_via_post(self):
        self.client.force_login(self.patient)
        response = self.client.post(
            reverse("appointments:book", args=[self.doctor.slug]),
            {"slot": self.slot.pk, "date": self.slot.date.isoformat(), "reason": "Pain"},
        )
        self.assertEqual(response.status_code, 302)
        appointment = Appointment.objects.get(patient=self.patient)
        self.assertRedirects(
            response, reverse("appointments:detail", args=[appointment.reference])
        )

    def test_post_without_slot_rejected(self):
        self.client.force_login(self.patient)
        response = self.client.post(
            reverse("appointments:book", args=[self.doctor.slug]), {"date": ""}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Appointment.objects.exists())


class AppointmentListDetailViewTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()
        self.patient_a = make_user("a@example.com")
        self.patient_b = make_user("b@example.com")
        slot = make_slot(self.doctor, future_day(5))
        self.appointment = services.book_slot(slot.pk, actor=self.patient_a)
        self.client = Client()

    def test_list_requires_login(self):
        response = self.client.get(reverse("appointments:list"))
        self.assertEqual(response.status_code, 302)

    def test_patient_list_shows_own(self):
        self.client.force_login(self.patient_a)
        response = self.client.get(reverse("appointments:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.appointment.reference)

    def test_detail_idor_returns_404(self):
        self.client.force_login(self.patient_b)
        response = self.client.get(
            reverse("appointments:detail", args=[self.appointment.reference])
        )
        self.assertEqual(response.status_code, 404)

    def test_owner_can_view_detail(self):
        self.client.force_login(self.patient_a)
        response = self.client.get(
            reverse("appointments:detail", args=[self.appointment.reference])
        )
        self.assertEqual(response.status_code, 200)


class CancelRescheduleViewTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()
        self.patient = make_user("patient@example.com")
        self.slot_a = make_slot(self.doctor, future_day(5), time(9, 0), time(9, 30))
        self.slot_b = make_slot(self.doctor, future_day(5), time(9, 30), time(10, 0))
        self.appointment = services.book_slot(self.slot_a.pk, actor=self.patient)
        self.client = Client()

    def test_cancel_get_and_post(self):
        self.client.force_login(self.patient)
        get_resp = self.client.get(
            reverse("appointments:cancel", args=[self.appointment.reference])
        )
        self.assertEqual(get_resp.status_code, 200)
        post_resp = self.client.post(
            reverse("appointments:cancel", args=[self.appointment.reference]),
            {"reason": "Changed plans"},
        )
        self.assertEqual(post_resp.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, AppointmentStatus.CANCELLED)

    def test_reschedule_get_and_post(self):
        self.client.force_login(self.patient)
        get_resp = self.client.get(
            reverse("appointments:reschedule", args=[self.appointment.reference])
        )
        self.assertEqual(get_resp.status_code, 200)
        post_resp = self.client.post(
            reverse("appointments:reschedule", args=[self.appointment.reference]),
            {"slot": self.slot_b.pk, "date": self.slot_b.date.isoformat()},
        )
        self.assertEqual(post_resp.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.slot, self.slot_b)

    def test_cancel_forbidden_for_other_patient(self):
        other = make_user("other@example.com")
        self.client.force_login(other)
        response = self.client.get(
            reverse("appointments:cancel", args=[self.appointment.reference])
        )
        self.assertEqual(response.status_code, 404)


# --------------------------------------------------------------------------
# Concurrency (MySQL only)
# --------------------------------------------------------------------------
@unittest.skipUnless(
    connection.vendor == "mysql",
    "Row-level locking concurrency test requires MySQL/InnoDB.",
)
class BookingConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def test_concurrent_booking_has_single_winner(self):
        doctor = make_doctor()
        slot = make_slot(doctor, future_day(5))
        patients = [
            make_user("c1@example.com"),
            make_user("c2@example.com"),
        ]
        results = []
        barrier = threading.Barrier(len(patients))

        def worker(patient):
            barrier.wait()
            try:
                services.book_slot(slot.pk, actor=patient)
                results.append("booked")
            except services.BookingError:
                results.append("blocked")
            finally:
                connection.close()

        threads = [threading.Thread(target=worker, args=(p,)) for p in patients]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(results.count("booked"), 1)
        self.assertEqual(Appointment.objects.filter(slot=slot).count(), 1)
