"""Tests for the role-based dashboards (Phase 6).

Covers: landing routing by role, per-role access control (anonymous/wrong role),
patient & doctor ownership, receptionist/admin visibility, search/filtering,
pagination safety, status transitions via the service layer, book-on-behalf, and
IDOR / CSRF / GET-safety protections.
"""
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from appointments.models import (
    Appointment,
    AppointmentSlot,
    AppointmentStatus,
    SlotStatus,
)
from clinic.models import Doctor, Speciality

User = get_user_model()
PASSWORD = "S3cret-pass!"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def make_user(email, role=User.Role.PATIENT, **kwargs):
    kwargs.setdefault("first_name", role.title())
    kwargs.setdefault("last_name", "User")
    return User.objects.create_user(email=email, password=PASSWORD, role=role, **kwargs)


def make_doctor(email="doc@example.com", *, speciality=None, **kwargs):
    user = kwargs.pop("user", None) or make_user(email, role=User.Role.DOCTOR)
    speciality = speciality or Speciality.objects.create(name=f"Spec {email}")
    return Doctor.objects.create(
        user=user,
        speciality=speciality,
        registration_number=f"REG-{email}",
        qualification="MBBS",
        **kwargs,
    )


def future_day(days=7):
    return timezone.localdate() + timedelta(days=days)


def make_slot(doctor, day, start=time(9, 0), status=SlotStatus.OPEN, end=None):
    if end is None:
        end = (datetime.combine(day, start) + timedelta(minutes=30)).time()
    return AppointmentSlot.objects.create(
        doctor=doctor, date=day, start_time=start, end_time=end, status=status
    )


def make_appointment(patient, doctor, day, *, start=time(9, 0), status=AppointmentStatus.REQUESTED):
    end = (datetime.combine(day, start) + timedelta(minutes=30)).time()
    slot = make_slot(doctor, day, start, status=SlotStatus.BOOKED, end=end)
    return Appointment.objects.create(
        patient=patient,
        doctor=doctor,
        slot=slot,
        date=day,
        start_time=start,
        end_time=end,
        status=status,
    )


# --------------------------------------------------------------------------
# Landing / routing
# --------------------------------------------------------------------------
class DashboardRoutingTests(TestCase):
    url = reverse("dashboards:landing")

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_patient_routed_to_patient_dashboard(self):
        self.client.force_login(make_user("p@example.com", User.Role.PATIENT))
        self.assertRedirects(self.client.get(self.url), reverse("dashboards:patient"))

    def test_doctor_routed_to_doctor_dashboard(self):
        doctor = make_doctor("d@example.com")
        self.client.force_login(doctor.user)
        self.assertRedirects(self.client.get(self.url), reverse("dashboards:doctor"))

    def test_receptionist_routed_to_receptionist_dashboard(self):
        self.client.force_login(make_user("r@example.com", User.Role.RECEPTIONIST))
        self.assertRedirects(
            self.client.get(self.url), reverse("dashboards:receptionist")
        )

    def test_admin_routed_to_admin_dashboard(self):
        self.client.force_login(make_user("a@example.com", User.Role.ADMIN))
        self.assertRedirects(self.client.get(self.url), reverse("dashboards:admin"))

    def test_superuser_routed_to_admin_dashboard(self):
        user = User.objects.create_superuser(email="root@example.com", password=PASSWORD)
        self.client.force_login(user)
        self.assertRedirects(self.client.get(self.url), reverse("dashboards:admin"))

    def test_unknown_role_fails_safely(self):
        user = make_user("weird@example.com", User.Role.PATIENT)
        User.objects.filter(pk=user.pk).update(role="MYSTERY")
        user.refresh_from_db()
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No dashboard")


# --------------------------------------------------------------------------
# Access control matrix
# --------------------------------------------------------------------------
class DashboardAccessTests(TestCase):
    def setUp(self):
        self.patient = make_user("p@example.com", User.Role.PATIENT)
        self.doctor = make_doctor("d@example.com")
        self.receptionist = make_user("r@example.com", User.Role.RECEPTIONIST)
        self.admin = make_user("a@example.com", User.Role.ADMIN)
        self.urls = {
            "patient": reverse("dashboards:patient"),
            "doctor": reverse("dashboards:doctor"),
            "receptionist": reverse("dashboards:receptionist"),
            "admin": reverse("dashboards:admin"),
        }

    def test_anonymous_redirected(self):
        for url in self.urls.values():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("accounts:login"), response.url)

    def test_patient_only_own_dashboard(self):
        self.client.force_login(self.patient)
        self.assertEqual(self.client.get(self.urls["patient"]).status_code, 200)
        for key in ("doctor", "receptionist", "admin"):
            self.assertEqual(self.client.get(self.urls[key]).status_code, 403)

    def test_doctor_only_own_dashboard(self):
        self.client.force_login(self.doctor.user)
        self.assertEqual(self.client.get(self.urls["doctor"]).status_code, 200)
        for key in ("patient", "receptionist", "admin"):
            self.assertEqual(self.client.get(self.urls[key]).status_code, 403)

    def test_receptionist_only_own_dashboard(self):
        self.client.force_login(self.receptionist)
        self.assertEqual(self.client.get(self.urls["receptionist"]).status_code, 200)
        for key in ("patient", "doctor", "admin"):
            self.assertEqual(self.client.get(self.urls[key]).status_code, 403)

    def test_admin_only_own_dashboard(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(self.urls["admin"]).status_code, 200)
        for key in ("patient", "doctor", "receptionist"):
            self.assertEqual(self.client.get(self.urls[key]).status_code, 403)


# --------------------------------------------------------------------------
# Patient dashboard
# --------------------------------------------------------------------------
class PatientDashboardTests(TestCase):
    def setUp(self):
        self.patient = make_user("p@example.com")
        self.other = make_user("other@example.com")
        self.doctor = make_doctor("d@example.com")
        self.mine = make_appointment(self.patient, self.doctor, future_day(5))
        self.theirs = make_appointment(
            self.other, self.doctor, future_day(6), start=time(10, 0)
        )

    def test_shows_only_own_appointments(self):
        self.client.force_login(self.patient)
        response = self.client.get(reverse("dashboards:patient"))
        pks = {a.pk for a in response.context["upcoming"]}
        self.assertIn(self.mine.pk, pks)
        self.assertNotIn(self.theirs.pk, pks)

    def test_history_lists_past(self):
        past = make_appointment(
            self.patient, self.doctor, future_day(-3), start=time(11, 0)
        )
        self.client.force_login(self.patient)
        response = self.client.get(reverse("dashboards:patient"))
        self.assertIn(past.pk, {a.pk for a in response.context["history"]})
        self.assertNotIn(past.pk, {a.pk for a in response.context["upcoming"]})

    def test_patient_cannot_manage_status(self):
        self.client.force_login(self.patient)
        response = self.client.get(reverse("dashboards:patient"))
        self.assertFalse(response.context["upcoming"][0].can_manage)

    def test_book_link_present(self):
        self.client.force_login(self.patient)
        response = self.client.get(reverse("dashboards:patient"))
        self.assertContains(response, reverse("doctor_list"))


# --------------------------------------------------------------------------
# Doctor dashboard
# --------------------------------------------------------------------------
class DoctorDashboardTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor("d@example.com")
        self.other_doctor = make_doctor("d2@example.com")
        self.patient = make_user("p@example.com")
        self.today = make_appointment(
            self.patient, self.doctor, timezone.localdate(), start=time(9, 0)
        )
        self.upcoming = make_appointment(
            self.patient, self.doctor, future_day(4), start=time(10, 0)
        )
        self.foreign = make_appointment(
            self.patient, self.other_doctor, future_day(4), start=time(11, 0)
        )

    def test_shows_only_own_schedule(self):
        self.client.force_login(self.doctor.user)
        response = self.client.get(reverse("dashboards:doctor"))
        all_pks = {
            a.pk
            for group in ("today", "upcoming", "past")
            for a in response.context[group]
        }
        self.assertIn(self.today.pk, all_pks)
        self.assertIn(self.upcoming.pk, all_pks)
        self.assertNotIn(self.foreign.pk, all_pks)

    def test_doctor_without_profile_renders(self):
        user = make_user("nodoc@example.com", User.Role.DOCTOR)
        self.client.force_login(user)
        response = self.client.get(reverse("dashboards:doctor"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no doctor profile")

    def test_doctor_can_confirm_own_appointment(self):
        self.client.force_login(self.doctor.user)
        response = self.client.post(
            reverse("dashboards:appointment_status", args=[self.upcoming.reference]),
            {"new_status": AppointmentStatus.CONFIRMED},
        )
        self.assertEqual(response.status_code, 302)
        self.upcoming.refresh_from_db()
        self.assertEqual(self.upcoming.status, AppointmentStatus.CONFIRMED)

    def test_doctor_cannot_touch_another_doctors_appointment(self):
        self.client.force_login(self.doctor.user)
        response = self.client.post(
            reverse("dashboards:appointment_status", args=[self.foreign.reference]),
            {"new_status": AppointmentStatus.CONFIRMED},
        )
        self.assertEqual(response.status_code, 404)
        self.foreign.refresh_from_db()
        self.assertEqual(self.foreign.status, AppointmentStatus.REQUESTED)

    def test_invalid_transition_rejected(self):
        self.client.force_login(self.doctor.user)
        response = self.client.post(
            reverse("dashboards:appointment_status", args=[self.upcoming.reference]),
            {"new_status": AppointmentStatus.COMPLETED},
        )
        self.assertEqual(response.status_code, 302)
        self.upcoming.refresh_from_db()
        self.assertEqual(self.upcoming.status, AppointmentStatus.REQUESTED)

    def test_unknown_status_rejected(self):
        self.client.force_login(self.doctor.user)
        self.client.post(
            reverse("dashboards:appointment_status", args=[self.upcoming.reference]),
            {"new_status": "BOGUS"},
        )
        self.upcoming.refresh_from_db()
        self.assertEqual(self.upcoming.status, AppointmentStatus.REQUESTED)

    def test_status_endpoint_rejects_get(self):
        self.client.force_login(self.doctor.user)
        response = self.client.get(
            reverse("dashboards:appointment_status", args=[self.upcoming.reference])
        )
        self.assertEqual(response.status_code, 405)

    def test_patient_cannot_change_status(self):
        self.client.force_login(self.patient)
        response = self.client.post(
            reverse("dashboards:appointment_status", args=[self.upcoming.reference]),
            {"new_status": AppointmentStatus.CONFIRMED},
        )
        self.assertEqual(response.status_code, 403)
        self.upcoming.refresh_from_db()
        self.assertEqual(self.upcoming.status, AppointmentStatus.REQUESTED)

    def test_csrf_enforced_on_status_post(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.doctor.user)
        response = csrf_client.post(
            reverse("dashboards:appointment_status", args=[self.upcoming.reference]),
            {"new_status": AppointmentStatus.CONFIRMED},
        )
        self.assertEqual(response.status_code, 403)
        self.upcoming.refresh_from_db()
        self.assertEqual(self.upcoming.status, AppointmentStatus.REQUESTED)


# --------------------------------------------------------------------------
# Receptionist dashboard
# --------------------------------------------------------------------------
class ReceptionistDashboardTests(TestCase):
    def setUp(self):
        self.receptionist = make_user("r@example.com", User.Role.RECEPTIONIST)
        self.patient = make_user("p@example.com")
        self.patient2 = make_user("p2@example.com")
        self.doctor = make_doctor("d@example.com")
        self.doctor2 = make_doctor("d2@example.com")
        self.a1 = make_appointment(self.patient, self.doctor, future_day(3))
        self.a2 = make_appointment(
            self.patient2, self.doctor2, future_day(4), start=time(10, 0),
            status=AppointmentStatus.CONFIRMED,
        )
        self.client.force_login(self.receptionist)

    def test_sees_all_appointments(self):
        response = self.client.get(reverse("dashboards:receptionist"))
        pks = {a.pk for a in response.context["appointments"]}
        self.assertEqual(pks, {self.a1.pk, self.a2.pk})

    def test_filter_by_status(self):
        response = self.client.get(
            reverse("dashboards:receptionist"), {"status": "CONFIRMED"}
        )
        pks = {a.pk for a in response.context["appointments"]}
        self.assertEqual(pks, {self.a2.pk})

    def test_filter_by_doctor(self):
        response = self.client.get(
            reverse("dashboards:receptionist"), {"doctor": self.doctor.pk}
        )
        pks = {a.pk for a in response.context["appointments"]}
        self.assertEqual(pks, {self.a1.pk})

    def test_filter_by_patient(self):
        response = self.client.get(
            reverse("dashboards:receptionist"), {"patient": self.patient.pk}
        )
        pks = {a.pk for a in response.context["appointments"]}
        self.assertEqual(pks, {self.a1.pk})

    def test_filter_by_reference(self):
        response = self.client.get(
            reverse("dashboards:receptionist"), {"reference": self.a2.reference}
        )
        pks = {a.pk for a in response.context["appointments"]}
        self.assertEqual(pks, {self.a2.pk})

    def test_scope_past_and_today(self):
        past = make_appointment(
            self.patient, self.doctor, future_day(-2), start=time(8, 0),
            status=AppointmentStatus.COMPLETED,
        )
        response = self.client.get(
            reverse("dashboards:receptionist"), {"scope": "past"}
        )
        pks = {a.pk for a in response.context["appointments"]}
        self.assertIn(past.pk, pks)
        self.assertNotIn(self.a1.pk, pks)

    def test_invalid_filters_do_not_error(self):
        response = self.client.get(
            reverse("dashboards:receptionist"),
            {"status": "NOPE", "doctor": "abc", "patient": "99999", "date": "not-a-date"},
        )
        self.assertEqual(response.status_code, 200)
        # All rows still shown because every bad filter is ignored.
        self.assertEqual(len(response.context["appointments"]), 2)

    def test_pagination_split(self):
        for i in range(12):
            make_appointment(
                self.patient,
                self.doctor,
                future_day(30 + i),
                start=time(9, 0),
            )
        response = self.client.get(reverse("dashboards:receptionist"))
        self.assertEqual(len(response.context["appointments"]), 10)
        self.assertTrue(response.context["page_obj"].has_next)

    def test_invalid_page_number_safe(self):
        response = self.client.get(
            reverse("dashboards:receptionist"), {"page": "999"}
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse("dashboards:receptionist"), {"page": "abc"}
        )
        self.assertEqual(response.status_code, 200)

    def test_querystring_preserves_filters(self):
        response = self.client.get(
            reverse("dashboards:receptionist"), {"status": "CONFIRMED"}
        )
        self.assertIn("status=CONFIRMED", response.context["querystring"])

    def test_receptionist_can_manage_status(self):
        response = self.client.get(reverse("dashboards:receptionist"))
        first = response.context["appointments"][0]
        self.assertTrue(first.can_manage)


# --------------------------------------------------------------------------
# Book on behalf
# --------------------------------------------------------------------------
class ReceptionistBookOnBehalfTests(TestCase):
    def setUp(self):
        self.receptionist = make_user("r@example.com", User.Role.RECEPTIONIST)
        self.patient = make_user("p@example.com")
        self.doctor = make_doctor("d@example.com")
        self.day = future_day(5)
        self.slot = make_slot(self.doctor, self.day, time(9, 0))
        self.client.force_login(self.receptionist)

    def test_get_renders(self):
        response = self.client.get(reverse("dashboards:receptionist_book"))
        self.assertEqual(response.status_code, 200)

    def test_get_with_doctor_shows_slots(self):
        response = self.client.get(
            reverse("dashboards:receptionist_book"),
            {
                "doctor": self.doctor.pk,
                "patient": self.patient.pk,
                "date": self.day.isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.patient.get_full_name())
        # The open slot appears as a bookable radio option.
        self.assertContains(response, f'value="{self.slot.pk}"')

    def test_books_on_behalf(self):
        response = self.client.post(
            reverse("dashboards:receptionist_book"),
            {
                "patient": self.patient.pk,
                "doctor": self.doctor.pk,
                "date": self.day.isoformat(),
                "slot": self.slot.pk,
            },
        )
        self.assertEqual(response.status_code, 302)
        appointment = Appointment.objects.get(patient=self.patient)
        self.assertEqual(appointment.doctor, self.doctor)
        self.assertEqual(appointment.status, AppointmentStatus.REQUESTED)

    def test_rejects_non_patient_patient(self):
        response = self.client.post(
            reverse("dashboards:receptionist_book"),
            {
                "patient": self.doctor.user.pk,
                "doctor": self.doctor.pk,
                "date": self.day.isoformat(),
                "slot": self.slot.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Appointment.objects.exists())

    def test_rejects_unknown_doctor(self):
        response = self.client.post(
            reverse("dashboards:receptionist_book"),
            {
                "patient": self.patient.pk,
                "doctor": 999999,
                "date": self.day.isoformat(),
                "slot": self.slot.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Appointment.objects.exists())

    def test_patient_cannot_book_on_behalf(self):
        self.client.force_login(self.patient)
        response = self.client.get(reverse("dashboards:receptionist_book"))
        self.assertEqual(response.status_code, 403)


# --------------------------------------------------------------------------
# Admin dashboard
# --------------------------------------------------------------------------
class AdminDashboardTests(TestCase):
    def setUp(self):
        self.admin = make_user("a@example.com", User.Role.ADMIN)
        self.patient = make_user("p@example.com")
        self.doctor = make_doctor("d@example.com")
        self.client.force_login(self.admin)

    def test_statistics(self):
        today = timezone.localdate()
        make_appointment(self.patient, self.doctor, today, start=time(9, 0),
                         status=AppointmentStatus.CONFIRMED)
        make_appointment(self.patient, self.doctor, future_day(3), start=time(10, 0))
        make_appointment(self.patient, self.doctor, future_day(-3), start=time(8, 0),
                         status=AppointmentStatus.COMPLETED)
        make_appointment(self.patient, self.doctor, future_day(4), start=time(7, 0),
                         status=AppointmentStatus.CANCELLED)

        response = self.client.get(reverse("dashboards:admin"))
        stats = response.context["stats"]
        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["today"], 1)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["cancelled"], 1)
        self.assertEqual(stats["upcoming"], 3)
        self.assertEqual(response.context["total_patients"], 1)
        self.assertEqual(response.context["total_doctors"], 1)

    def test_status_breakdown(self):
        make_appointment(self.patient, self.doctor, future_day(2),
                         status=AppointmentStatus.CONFIRMED)
        response = self.client.get(reverse("dashboards:admin"))
        breakdown = {row["value"]: row["count"] for row in response.context["status_breakdown"]}
        self.assertEqual(breakdown[AppointmentStatus.CONFIRMED], 1)

    def test_admin_dashboard_lists_appointments(self):
        appt = make_appointment(self.patient, self.doctor, future_day(2))
        response = self.client.get(reverse("dashboards:admin"))
        self.assertIn(appt.pk, {a.pk for a in response.context["appointments"]})


# --------------------------------------------------------------------------
# Read-only safety
# --------------------------------------------------------------------------
class DashboardReadOnlyTests(TestCase):
    def test_get_dashboards_do_not_mutate(self):
        patient = make_user("p@example.com")
        doctor = make_doctor("d@example.com")
        appt = make_appointment(patient, doctor, future_day(3))
        before = (appt.status, appt.updated_at)
        self.client.force_login(doctor.user)
        self.client.get(reverse("dashboards:doctor"))
        appt.refresh_from_db()
        self.assertEqual((appt.status, appt.updated_at), before)
