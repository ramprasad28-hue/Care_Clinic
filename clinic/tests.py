"""Tests for the clinic app: models, self-service access control, and admin.

Runnable via either:
    python manage.py test
    pytest
"""
from datetime import date, time

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db.models import ProtectedError
from django.test import RequestFactory, TestCase
from django.urls import reverse

from clinic.admin import AvailabilityRuleAdmin, DoctorAdmin, SpecialityAdmin
from clinic.models import AvailabilityRule, Doctor, DoctorLeave, Speciality, Weekday

User = get_user_model()
PASSWORD = "S3cret-pass!"


def make_user(email="doctor@example.com", role=User.Role.DOCTOR, **kwargs):
    return User.objects.create_user(email=email, password=PASSWORD, role=role, **kwargs)


def make_speciality(name="Cardiology", **kwargs):
    return Speciality.objects.create(name=name, **kwargs)


def make_doctor(speciality=None, email="doctor@example.com", **kwargs):
    user = kwargs.pop("user", None) or make_user(email=email)
    speciality = speciality or make_speciality()
    defaults = {
        "registration_number": f"REG-{email}",
        "qualification": "MBBS",
    }
    defaults.update(kwargs)
    return Doctor.objects.create(user=user, speciality=speciality, **defaults)


# --------------------------------------------------------------------------
# Speciality
# --------------------------------------------------------------------------
class SpecialityModelTests(TestCase):
    def test_create_speciality(self):
        spec = make_speciality("Cardiology")
        self.assertEqual(spec.name, "Cardiology")
        self.assertTrue(spec.is_active)
        self.assertTrue(spec.created_at and spec.updated_at)

    def test_slug_auto_generated(self):
        spec = make_speciality("General Medicine")
        self.assertEqual(spec.slug, "general-medicine")

    def test_duplicate_name_rejected(self):
        make_speciality("Cardiology")
        with self.assertRaises(ValidationError):
            make_speciality("Cardiology")

    def test_duplicate_slug_rejected(self):
        make_speciality("Cardiology")
        with self.assertRaises(ValidationError):
            Speciality.objects.create(name="Cardiology Two", slug="cardiology")

    def test_active_scope(self):
        make_speciality("Cardiology", is_active=True)
        make_speciality("Dermatology", is_active=False)
        self.assertEqual(Speciality.objects.active().count(), 1)


# --------------------------------------------------------------------------
# Doctor
# --------------------------------------------------------------------------
class DoctorModelTests(TestCase):
    def test_create_doctor(self):
        doctor = make_doctor()
        self.assertEqual(doctor.user.role, User.Role.DOCTOR)
        self.assertTrue(doctor.is_accepting_appointments)
        self.assertEqual(doctor.slot_length_minutes, 30)

    def test_doctor_requires_doctor_role_user(self):
        patient = make_user(email="patient@example.com", role=User.Role.PATIENT)
        with self.assertRaises(ValidationError):
            Doctor.objects.create(
                user=patient,
                speciality=make_speciality(),
                registration_number="REG-P",
                qualification="MBBS",
            )

    def test_registration_number_unique(self):
        spec = make_speciality("Cardiology")
        make_doctor(spec, email="a@example.com", registration_number="REG-1")
        with self.assertRaises(ValidationError):
            make_doctor(spec, email="b@example.com", registration_number="REG-1")

    def test_one_profile_per_user(self):
        doctor = make_doctor()
        with self.assertRaises(ValidationError):
            Doctor.objects.create(
                user=doctor.user,
                speciality=doctor.speciality,
                registration_number="REG-OTHER",
                qualification="MBBS",
            )

    def test_speciality_is_protected(self):
        doctor = make_doctor()
        with self.assertRaises(ProtectedError):
            doctor.speciality.delete()

    def test_public_scope(self):
        spec = make_speciality("Cardiology")
        accepting = make_doctor(spec, email="a@example.com")
        make_doctor(spec, email="b@example.com", is_accepting_appointments=False)
        self.assertEqual(list(Doctor.objects.public()), [accepting])


# --------------------------------------------------------------------------
# AvailabilityRule
# --------------------------------------------------------------------------
class AvailabilityRuleModelTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()

    def test_create_valid_rule(self):
        rule = AvailabilityRule.objects.create(
            doctor=self.doctor,
            weekday=Weekday.MONDAY,
            start_time=time(9, 0),
            end_time=time(13, 0),
        )
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.effective_slot_length_minutes, 30)  # doctor default

    def test_end_time_must_be_after_start(self):
        with self.assertRaises(ValidationError):
            AvailabilityRule.objects.create(
                doctor=self.doctor,
                weekday=Weekday.MONDAY,
                start_time=time(13, 0),
                end_time=time(9, 0),
            )

    def test_slot_duration_must_be_positive(self):
        with self.assertRaises(ValidationError):
            AvailabilityRule.objects.create(
                doctor=self.doctor,
                weekday=Weekday.MONDAY,
                start_time=time(9, 0),
                end_time=time(13, 0),
                slot_length_minutes=0,
            )

    def test_duplicate_window_rejected(self):
        AvailabilityRule.objects.create(
            doctor=self.doctor,
            weekday=Weekday.MONDAY,
            start_time=time(9, 0),
            end_time=time(13, 0),
        )
        with self.assertRaises(ValidationError):
            AvailabilityRule.objects.create(
                doctor=self.doctor,
                weekday=Weekday.MONDAY,
                start_time=time(9, 0),
                end_time=time(13, 0),
            )

    def test_overlapping_window_rejected(self):
        AvailabilityRule.objects.create(
            doctor=self.doctor,
            weekday=Weekday.MONDAY,
            start_time=time(9, 0),
            end_time=time(13, 0),
        )
        with self.assertRaises(ValidationError):
            AvailabilityRule.objects.create(
                doctor=self.doctor,
                weekday=Weekday.MONDAY,
                start_time=time(12, 0),
                end_time=time(14, 0),
            )

    def test_non_overlapping_window_allowed(self):
        AvailabilityRule.objects.create(
            doctor=self.doctor,
            weekday=Weekday.MONDAY,
            start_time=time(9, 0),
            end_time=time(13, 0),
        )
        rule = AvailabilityRule.objects.create(
            doctor=self.doctor,
            weekday=Weekday.MONDAY,
            start_time=time(13, 0),
            end_time=time(17, 0),
        )
        self.assertIsNotNone(rule.pk)

    def test_rule_slot_length_overrides_doctor(self):
        rule = AvailabilityRule.objects.create(
            doctor=self.doctor,
            weekday=Weekday.TUESDAY,
            start_time=time(9, 0),
            end_time=time(11, 0),
            slot_length_minutes=20,
        )
        self.assertEqual(rule.effective_slot_length_minutes, 20)


# --------------------------------------------------------------------------
# DoctorLeave
# --------------------------------------------------------------------------
class DoctorLeaveModelTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()

    def test_create_valid_leave(self):
        leave = DoctorLeave.objects.create(
            doctor=self.doctor,
            start_date=date(2026, 1, 10),
            end_date=date(2026, 1, 12),
            reason="Conference",
        )
        self.assertIsNotNone(leave.pk)

    def test_single_day_leave_allowed(self):
        leave = DoctorLeave.objects.create(
            doctor=self.doctor,
            start_date=date(2026, 1, 10),
            end_date=date(2026, 1, 10),
        )
        self.assertIsNotNone(leave.pk)

    def test_end_before_start_rejected(self):
        with self.assertRaises(ValidationError):
            DoctorLeave.objects.create(
                doctor=self.doctor,
                start_date=date(2026, 1, 12),
                end_date=date(2026, 1, 10),
            )


# --------------------------------------------------------------------------
# Doctor self-service access control
# --------------------------------------------------------------------------
class AvailabilityAccessTests(TestCase):
    def setUp(self):
        self.factory_spec = make_speciality("Cardiology")
        self.doctor = make_doctor(self.factory_spec, email="owner@example.com")
        self.other = make_doctor(self.factory_spec, email="other@example.com")
        self.own_rule = AvailabilityRule.objects.create(
            doctor=self.doctor, weekday=Weekday.MONDAY,
            start_time=time(9, 0), end_time=time(13, 0),
        )
        self.other_rule = AvailabilityRule.objects.create(
            doctor=self.other, weekday=Weekday.TUESDAY,
            start_time=time(9, 0), end_time=time(13, 0),
        )
        self.list_url = reverse("clinic:availability_list")

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_patient_forbidden(self):
        self.client.force_login(make_user(email="p@example.com", role=User.Role.PATIENT))
        self.assertEqual(self.client.get(self.list_url).status_code, 403)

    def test_doctor_without_profile_forbidden(self):
        self.client.force_login(make_user(email="noprofile@example.com", role=User.Role.DOCTOR))
        self.assertEqual(self.client.get(self.list_url).status_code, 403)

    def test_doctor_sees_only_own_rules(self):
        self.client.force_login(self.doctor.user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Monday")
        self.assertNotContains(response, "Tuesday")

    def test_doctor_cannot_edit_another_doctors_rule(self):
        self.client.force_login(self.doctor.user)
        url = reverse("clinic:availability_edit", kwargs={"pk": self.other_rule.pk})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_doctor_cannot_delete_another_doctors_rule(self):
        self.client.force_login(self.doctor.user)
        url = reverse("clinic:availability_delete", kwargs={"pk": self.other_rule.pk})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_doctor_can_edit_own_rule(self):
        self.client.force_login(self.doctor.user)
        url = reverse("clinic:availability_edit", kwargs={"pk": self.own_rule.pk})
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_create_ignores_submitted_doctor_id(self):
        # A doctor cannot attribute a rule to another doctor by posting the id.
        self.client.force_login(self.doctor.user)
        response = self.client.post(
            reverse("clinic:availability_add"),
            {
                "weekday": Weekday.WEDNESDAY,
                "start_time": "09:00",
                "end_time": "11:00",
                "slot_length_minutes": "",
                "is_active": "on",
                "doctor": self.other.pk,
            },
        )
        self.assertEqual(response.status_code, 302)
        rule = AvailabilityRule.objects.get(doctor=self.doctor, weekday=Weekday.WEDNESDAY)
        self.assertEqual(rule.doctor, self.doctor)


class LeaveAccessTests(TestCase):
    def setUp(self):
        spec = make_speciality("Cardiology")
        self.doctor = make_doctor(spec, email="owner@example.com")
        self.other = make_doctor(spec, email="other@example.com")
        self.own_leave = DoctorLeave.objects.create(
            doctor=self.doctor, start_date=date(2026, 2, 1), end_date=date(2026, 2, 2)
        )
        self.other_leave = DoctorLeave.objects.create(
            doctor=self.other, start_date=date(2026, 3, 1), end_date=date(2026, 3, 2)
        )

    def test_anonymous_redirected(self):
        self.assertEqual(self.client.get(reverse("clinic:leave_list")).status_code, 302)

    def test_patient_forbidden(self):
        self.client.force_login(make_user(email="p@example.com", role=User.Role.PATIENT))
        self.assertEqual(self.client.get(reverse("clinic:leave_list")).status_code, 403)

    def test_doctor_cannot_delete_another_doctors_leave(self):
        self.client.force_login(self.doctor.user)
        url = reverse("clinic:leave_delete", kwargs={"pk": self.other_leave.pk})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_doctor_sees_only_own_leave(self):
        self.client.force_login(self.doctor.user)
        response = self.client.get(reverse("clinic:leave_list"))
        self.assertContains(response, "2026-02-01")
        self.assertNotContains(response, "2026-03-01")

    def test_create_forces_ownership(self):
        self.client.force_login(self.doctor.user)
        response = self.client.post(
            reverse("clinic:leave_add"),
            {
                "start_date": "2026-04-01",
                "end_date": "2026-04-03",
                "reason": "Training",
                "doctor": self.other.pk,
            },
        )
        self.assertEqual(response.status_code, 302)
        leave = DoctorLeave.objects.get(doctor=self.doctor, start_date=date(2026, 4, 1))
        self.assertEqual(leave.doctor, self.doctor)


# --------------------------------------------------------------------------
# Admin authorization
# --------------------------------------------------------------------------
class AdminAuthorizationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        spec = make_speciality("Cardiology")
        self.doctor = make_doctor(spec, email="owner@example.com")
        self.other = make_doctor(spec, email="other@example.com")
        self.speciality_admin = SpecialityAdmin(Speciality, self.site)
        self.doctor_admin = DoctorAdmin(Doctor, self.site)
        self.rule_admin = AvailabilityRuleAdmin(AvailabilityRule, self.site)

    def _request(self, user):
        request = self.factory.get("/admin/")
        request.user = user
        return request

    def test_non_admin_cannot_manage_specialities(self):
        request = self._request(self.doctor.user)
        self.assertFalse(self.speciality_admin.has_change_permission(request))
        self.assertFalse(self.speciality_admin.has_add_permission(request))
        self.assertFalse(self.speciality_admin.has_delete_permission(request))

    def test_non_admin_cannot_manage_doctors(self):
        request = self._request(self.doctor.user)
        self.assertFalse(self.doctor_admin.has_change_permission(request))

    def test_admin_role_can_manage_specialities_and_doctors(self):
        request = self._request(make_user(email="admin@example.com", role=User.Role.ADMIN))
        self.assertTrue(self.speciality_admin.has_change_permission(request))
        self.assertTrue(self.doctor_admin.has_change_permission(request))

    def test_superuser_can_manage(self):
        request = self._request(
            User.objects.create_superuser(email="root@example.com", password=PASSWORD)
        )
        self.assertTrue(self.speciality_admin.has_change_permission(request))
        self.assertTrue(self.doctor_admin.has_change_permission(request))

    def test_availability_queryset_scoped_to_doctor(self):
        own = AvailabilityRule.objects.create(
            doctor=self.doctor, weekday=Weekday.MONDAY,
            start_time=time(9, 0), end_time=time(13, 0),
        )
        AvailabilityRule.objects.create(
            doctor=self.other, weekday=Weekday.TUESDAY,
            start_time=time(9, 0), end_time=time(13, 0),
        )
        request = self._request(self.doctor.user)
        self.assertEqual(list(self.rule_admin.get_queryset(request)), [own])

    def test_availability_object_permission_is_ownership_scoped(self):
        own = AvailabilityRule.objects.create(
            doctor=self.doctor, weekday=Weekday.MONDAY,
            start_time=time(9, 0), end_time=time(13, 0),
        )
        other = AvailabilityRule.objects.create(
            doctor=self.other, weekday=Weekday.TUESDAY,
            start_time=time(9, 0), end_time=time(13, 0),
        )
        request = self._request(self.doctor.user)
        self.assertTrue(self.rule_admin.has_change_permission(request, own))
        self.assertFalse(self.rule_admin.has_change_permission(request, other))

    def test_admin_save_model_forces_doctor_ownership(self):
        request = self._request(self.doctor.user)
        obj = AvailabilityRule(
            doctor=self.other, weekday=Weekday.THURSDAY,
            start_time=time(9, 0), end_time=time(10, 0),
        )
        self.rule_admin.save_model(request, obj, form=None, change=False)
        obj.refresh_from_db()
        self.assertEqual(obj.doctor, self.doctor)

    def test_patient_cannot_access_availability_admin(self):
        request = self._request(make_user(email="p@example.com", role=User.Role.PATIENT))
        self.assertFalse(self.rule_admin.has_module_permission(request))
        self.assertFalse(self.rule_admin.has_view_permission(request))


# --------------------------------------------------------------------------
# seed_clinic command
# --------------------------------------------------------------------------
class SeedClinicCommandTests(TestCase):
    def test_seed_creates_data(self):
        call_command("seed_clinic")
        self.assertEqual(Speciality.objects.count(), 5)
        self.assertEqual(Doctor.objects.count(), 3)
        self.assertTrue(AvailabilityRule.objects.exists())
        self.assertTrue(DoctorLeave.objects.exists())

    def test_seed_is_idempotent(self):
        call_command("seed_clinic")
        call_command("seed_clinic")
        self.assertEqual(Speciality.objects.count(), 5)
        self.assertEqual(Doctor.objects.count(), 3)
        self.assertEqual(User.objects.filter(role=User.Role.DOCTOR).count(), 3)
