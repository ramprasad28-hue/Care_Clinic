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
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from clinic.admin import AvailabilityRuleAdmin, DoctorAdmin, SpecialityAdmin
from clinic.forms import (
    ACCOUNT_MODE_EXISTING,
    ACCOUNT_MODE_NEW,
    DoctorAdminForm,
)
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
# OneDayAvailability
# --------------------------------------------------------------------------
class OneDayAvailabilityModelTests(TestCase):
    def setUp(self):
        self.doctor = make_doctor()

    def test_create_valid_one_day_availability(self):
        from clinic.models import OneDayAvailability
        
        one_day = OneDayAvailability.objects.create(
            doctor=self.doctor,
            date=date(2026, 10, 25),
            start_time=time(10, 0),
            end_time=time(14, 0),
        )
        self.assertTrue(one_day.is_active)
        self.assertEqual(one_day.effective_slot_length_minutes, 30)  # doctor default

    def test_end_time_must_be_after_start(self):
        from clinic.models import OneDayAvailability
        
        with self.assertRaises(ValidationError):
            OneDayAvailability.objects.create(
                doctor=self.doctor,
                date=date(2026, 10, 25),
                start_time=time(14, 0),
                end_time=time(10, 0),
            )

    def test_slot_duration_must_be_positive(self):
        from clinic.models import OneDayAvailability
        
        with self.assertRaises(ValidationError):
            OneDayAvailability.objects.create(
                doctor=self.doctor,
                date=date(2026, 10, 25),
                start_time=time(10, 0),
                end_time=time(14, 0),
                slot_length_minutes=0,
            )

    def test_rule_slot_length_overrides_doctor(self):
        from clinic.models import OneDayAvailability
        
        one_day = OneDayAvailability.objects.create(
            doctor=self.doctor,
            date=date(2026, 10, 25),
            start_time=time(10, 0),
            end_time=time(14, 0),
            slot_length_minutes=20,
        )
        self.assertEqual(one_day.effective_slot_length_minutes, 20)

    def test_leave_date_rejected(self):
        from clinic.models import OneDayAvailability
        
        # Create leave for the target date
        DoctorLeave.objects.create(
            doctor=self.doctor,
            start_date=date(2026, 10, 25),
            end_date=date(2026, 10, 25),
            reason="Conference",
        )
        
        # Attempting to add one-day availability on leave date should fail
        with self.assertRaises(ValidationError) as cm:
            OneDayAvailability.objects.create(
                doctor=self.doctor,
                date=date(2026, 10, 25),
                start_time=time(10, 0),
                end_time=time(14, 0),
            )
        self.assertIn("on leave", str(cm.exception))

    def test_overlapping_weekly_rule_rejected(self):
        from clinic.models import OneDayAvailability
        
        # Create a weekly Monday rule
        target_date = date(2026, 10, 26)  # Monday
        AvailabilityRule.objects.create(
            doctor=self.doctor,
            weekday=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(13, 0),
            is_active=True,
        )
        
        # Overlapping one-day availability should be rejected
        with self.assertRaises(ValidationError) as cm:
            OneDayAvailability.objects.create(
                doctor=self.doctor,
                date=target_date,
                start_time=time(12, 0),
                end_time=time(14, 0),
            )
        self.assertIn("overlaps", str(cm.exception))

    def test_non_overlapping_weekly_rule_allowed(self):
        from clinic.models import OneDayAvailability
        
        # Create a weekly Monday rule
        target_date = date(2026, 10, 26)  # Monday
        AvailabilityRule.objects.create(
            doctor=self.doctor,
            weekday=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(13, 0),
            is_active=True,
        )
        
        # Adjacent one-day availability should be allowed
        one_day = OneDayAvailability.objects.create(
            doctor=self.doctor,
            date=target_date,
            start_time=time(13, 0),
            end_time=time(17, 0),
        )
        self.assertIsNotNone(one_day.pk)

    def test_overlapping_one_day_rules_rejected(self):
        from clinic.models import OneDayAvailability
        
        target_date = date(2026, 10, 25)
        OneDayAvailability.objects.create(
            doctor=self.doctor,
            date=target_date,
            start_time=time(9, 0),
            end_time=time(13, 0),
            is_active=True,
        )
        
        # Overlapping one-day availability should be rejected
        with self.assertRaises(ValidationError) as cm:
            OneDayAvailability.objects.create(
                doctor=self.doctor,
                date=target_date,
                start_time=time(12, 0),
                end_time=time(14, 0),
            )
        self.assertIn("overlaps", str(cm.exception))

    def test_inactive_weekly_rule_does_not_conflict(self):
        from clinic.models import OneDayAvailability
        
        # Create an inactive weekly rule
        target_date = date(2026, 10, 26)  # Monday
        AvailabilityRule.objects.create(
            doctor=self.doctor,
            weekday=target_date.weekday(),
            start_time=time(9, 0),
            end_time=time(13, 0),
            is_active=False,
        )
        
        # Overlapping one-day availability should be allowed since weekly is inactive
        one_day = OneDayAvailability.objects.create(
            doctor=self.doctor,
            date=target_date,
            start_time=time(10, 0),
            end_time=time(14, 0),
        )
        self.assertIsNotNone(one_day.pk)

    def test_different_dates_allowed(self):
        from clinic.models import OneDayAvailability
        
        OneDayAvailability.objects.create(
            doctor=self.doctor,
            date=date(2026, 10, 25),
            start_time=time(9, 0),
            end_time=time(13, 0),
        )
        
        # Different date with same time should be allowed
        one_day = OneDayAvailability.objects.create(
            doctor=self.doctor,
            date=date(2026, 10, 26),
            start_time=time(9, 0),
            end_time=time(13, 0),
        )
        self.assertIsNotNone(one_day.pk)

    def test_different_doctors_allowed(self):
        from clinic.models import OneDayAvailability
        
        other_speciality = make_speciality("Neurology")
        other_doctor = make_doctor(email="other@example.com", speciality=other_speciality)
        
        OneDayAvailability.objects.create(
            doctor=self.doctor,
            date=date(2026, 10, 25),
            start_time=time(9, 0),
            end_time=time(13, 0),
        )
        
        # Same date/time for different doctor should be allowed
        one_day = OneDayAvailability.objects.create(
            doctor=other_doctor,
            date=date(2026, 10, 25),
            start_time=time(9, 0),
            end_time=time(13, 0),
        )
        self.assertIsNotNone(one_day.pk)


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
        self.assertEqual(Speciality.objects.count(), 9)
        self.assertEqual(Doctor.objects.count(), 8)
        self.assertTrue(AvailabilityRule.objects.exists())
        self.assertTrue(DoctorLeave.objects.exists())

    def test_seed_is_idempotent(self):
        call_command("seed_clinic")
        call_command("seed_clinic")
        self.assertEqual(Speciality.objects.count(), 9)
        self.assertEqual(Doctor.objects.count(), 8)
        self.assertEqual(User.objects.filter(role=User.Role.DOCTOR).count(), 8)


class SeedExpansionTests(TestCase):
    """Expanded demo dataset: four specialities, five doctors (batch 4)."""

    NEW_SPECIALITIES = (
        ("Neurology", "neurology"),
        ("Ear, Nose & Throat", "ear-nose-throat"),
        ("Ophthalmology", "ophthalmology"),
        ("Gynaecology", "gynaecology"),
    )

    NEW_DOCTORS = {
        "dr.sabari@careclinic.example": "Neurology",
        "dr.prabhakaran@careclinic.example": "Ear, Nose & Throat",
        "dr.sanjay.krishna@careclinic.example": "Ophthalmology",
        "dr.radha.krishnan@careclinic.example": "Gynaecology",
        "dr.swetha@careclinic.example": "General Medicine",
    }

    def seed(self):
        call_command("seed_clinic")

    def test_four_new_specialities_created_active_with_valid_slugs(self):
        self.seed()
        for name, slug in self.NEW_SPECIALITIES:
            spec = Speciality.objects.filter(name=name).first()
            self.assertIsNotNone(spec, name)
            self.assertTrue(spec.is_active, name)
            self.assertEqual(spec.slug, slug, name)

    def test_five_new_doctor_users_have_doctor_role(self):
        self.seed()
        for email in self.NEW_DOCTORS:
            user = User.objects.filter(email=email).first()
            self.assertIsNotNone(user, email)
            self.assertEqual(user.role, User.Role.DOCTOR, email)
            self.assertEqual(user.doctor.user, user, email)  # exactly one related

    def test_profiles_point_to_intended_specialities(self):
        self.seed()
        for email, speciality in self.NEW_DOCTORS.items():
            doctor = User.objects.get(email=email).doctor
            self.assertEqual(doctor.speciality.name, speciality, email)
            self.assertTrue(doctor.is_accepting_appointments, email)

    def test_demo_registration_identifiers_unique(self):
        self.seed()
        numbers = [
            User.objects.get(email=email).doctor.registration_number
            for email in self.NEW_DOCTORS
        ]
        self.assertEqual(len(numbers), len(set(numbers)))
        for number in numbers:
            self.assertTrue(number.startswith("DEMO-REG-"), number)

    def test_new_doctors_have_valid_availability_rules(self):
        self.seed()
        # 8 doctors x 4 seed windows, all saved through full_clean (valid).
        self.assertEqual(AvailabilityRule.objects.count(), 32)
        for email in self.NEW_DOCTORS:
            doctor = User.objects.get(email=email).doctor
            self.assertEqual(
                doctor.availability_rules.filter(is_active=True).count(), 4, email
            )

    def test_new_demo_profiles_marked_unverified_with_no_fee(self):
        self.seed()
        for email in self.NEW_DOCTORS:
            doctor = User.objects.get(email=email).doctor
            self.assertIn("not verified", doctor.qualification, email)
            self.assertIsNone(doctor.consultation_fee, email)

    def test_rerun_keeps_existing_usable_password(self):
        user = User.objects.create_user(
            email="dr.swetha@careclinic.example",
            password="Us3r-picked-pw!",
            role=User.Role.DOCTOR,
        )
        self.assertTrue(user.check_password("Us3r-picked-pw!"))
        self.seed()
        user.refresh_from_db()
        self.assertTrue(user.check_password("Us3r-picked-pw!"))

    def test_role_conflict_fails_safely_without_changes(self):
        make_user(email="dr.swetha@careclinic.example", role=User.Role.PATIENT)
        before = User.objects.count()
        with self.assertRaises(Exception):
            call_command("seed_clinic")
        self.assertEqual(User.objects.count(), before)
        self.assertEqual(Doctor.objects.count(), 0)
        self.assertEqual(Speciality.objects.count(), 0)

    def test_pre_existing_other_specialities_untouched(self):
        psych = make_speciality("Psychiatrist")
        self.seed()
        psych.refresh_from_db()
        self.assertEqual(psych.name, "Psychiatrist")
        self.assertTrue(psych.is_active)
        # Exactly one Psychiatry-family record, no duplicates.
        self.assertEqual(
            Speciality.objects.filter(name__icontains="psychiat").count(), 1
        )


# --------------------------------------------------------------------------
# Presentation contracts (Phase 7.5 / Phase 9)
# --------------------------------------------------------------------------
class ClinicTemplatePresentationTests(TestCase):
    """Guards the editorial presentation contracts of the self-service pages.

    These are presentation-only: they protect the accessible table headers, the
    editorial page-head rule, and the confirm-panel accessible name without
    asserting any new behaviour.
    """

    def setUp(self):
        spec = make_speciality("Cardiology")
        self.doctor = make_doctor(spec, email="owner@example.com")
        self.rule = AvailabilityRule.objects.create(
            doctor=self.doctor, weekday=Weekday.MONDAY,
            start_time=time(9, 0), end_time=time(13, 0),
        )
        self.leave = DoctorLeave.objects.create(
            doctor=self.doctor, start_date=date(2026, 2, 1), end_date=date(2026, 2, 2),
        )
        self.client.force_login(self.doctor.user)

    def test_tables_keep_scoped_headers(self):
        self.assertContains(self.client.get(reverse("clinic:availability_list")), 'scope="col"')
        self.assertContains(self.client.get(reverse("clinic:leave_list")), 'scope="col"')

    def test_list_and_form_pages_use_editorial_rule(self):
        for name in (
            "clinic:availability_list",
            "clinic:leave_list",
            "clinic:availability_add",
            "clinic:leave_add",
        ):
            self.assertContains(self.client.get(reverse(name)), "section-rule", msg_prefix=name)

    def test_confirmation_panels_have_accessible_name(self):
        rule_page = self.client.get(
            reverse("clinic:availability_delete", kwargs={"pk": self.rule.pk})
        )
        self.assertContains(rule_page, 'aria-labelledby="delete-availability-heading"')
        leave_page = self.client.get(
            reverse("clinic:leave_delete", kwargs={"pk": self.leave.pk})
        )
        self.assertContains(leave_page, 'aria-labelledby="delete-leave-heading"')


# --------------------------------------------------------------------------
# Admin: Add Doctor — dual account mode (existing user / new account)
# --------------------------------------------------------------------------
FRESH_PASSWORD = "Fresh-Treat!42"


class DoctorAdminAddFormTests(TestCase):
    """DoctorAdminForm dual account-mode on the admin Add doctor form."""

    def setUp(self):
        self.speciality = make_speciality("Cardiology")
        self.existing_doctor_user = make_user(
            email="eligible@example.com", role=User.Role.DOCTOR
        )
        self.patient_user = make_user(
            email="patient@example.com", role=User.Role.PATIENT
        )
        make_doctor(self.speciality, email="takenprofile@example.com")

    def base_data(self, **overrides):
        data = {
            "account_mode": ACCOUNT_MODE_NEW,
            "new_first_name": "Nyasha",
            "new_last_name": "Moyo",
            "new_email": "newdoctor@example.com",
            "new_phone": "9876543210",
            "new_password1": FRESH_PASSWORD,
            "new_password2": FRESH_PASSWORD,
            "registration_number": "REG-NEW-1",
            "qualification": "MBBS, MD",
            "slot_length_minutes": 30,
            "speciality": self.speciality.pk,
        }
        data.update(overrides)
        return data

    def form(self, data, files=None):
        return DoctorAdminForm(data=data, files=files)

    # -- new account mode ------------------------------------------------
    def test_new_account_mode_creates_doctor_with_new_doctor_role_account(self):
        before_doctors = Doctor.objects.count()
        form = self.form(self.base_data())
        self.assertTrue(form.is_valid(), form.errors)
        doctor = form.save()

        self.assertEqual(doctor.user.email, "newdoctor@example.com")
        self.assertEqual(doctor.user.get_full_name(), "Nyasha Moyo")
        self.assertEqual(doctor.user.role, User.Role.DOCTOR)
        self.assertFalse(doctor.user.is_staff)
        self.assertFalse(doctor.user.is_superuser)
        self.assertTrue(doctor.user.check_password(FRESH_PASSWORD))
        self.assertEqual(Doctor.objects.count(), before_doctors + 1)
        self.assertEqual(doctor.speciality, self.speciality)

    def test_new_account_mode_rejects_duplicate_email(self):
        form = self.form(self.base_data(new_email="patient@example.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("new_email", form.errors)
        self.assertFalse(Doctor.objects.filter(user__email="patient@example.com").exists())

    def test_new_account_mode_rejects_mismatched_passwords(self):
        form = self.form(self.base_data(new_password2="Fresh-Treat!43"))
        self.assertFalse(form.is_valid())
        self.assertIn("new_password2", form.errors)

    def test_new_account_mode_enforces_password_site_policy(self):
        form = self.form(self.base_data(new_password1="short", new_password2="short"))
        self.assertFalse(form.is_valid())
        self.assertIn("new_password1", form.errors)
        self.assertFalse(User.objects.filter(email="newdoctor@example.com").exists())

    def test_new_account_mode_requires_name_email_and_passwords(self):
        form = self.form(
            {
                "account_mode": ACCOUNT_MODE_NEW,
                "registration_number": "REG-NEW-2",
                "qualification": "MBBS",
                "speciality": self.speciality.pk,
            }
        )
        self.assertFalse(form.is_valid())
        for field in ("new_first_name", "new_email", "new_password1", "new_password2"):
            self.assertIn(field, form.errors, field)
        self.assertEqual(User.objects.count(), 3)

    def test_failed_doctor_validation_leaves_no_orphaned_user_account(self):
        # Valid account data but a profile-level unique conflict (duplicate
        # registration number): nothing must persist on either side.
        before_users = User.objects.count()
        form = self.form(
            self.base_data(registration_number="REG-takenprofile@example.com")
        )
        self.assertFalse(form.is_valid())
        self.assertIn("registration_number", form.errors)
        self.assertEqual(User.objects.count(), before_users)
        self.assertEqual(Doctor.objects.count(), 1)

    def test_new_account_mode_ignores_tampered_user_choice(self):
        # A manually forged POST must not be able to attach an arbitrary
        # user in "new account" mode; the account fields decide the outcome.
        form = self.form(self.base_data(user=self.existing_doctor_user.pk))
        self.assertTrue(form.is_valid(), form.errors)
        doctor = form.save()
        self.assertEqual(doctor.user.email, "newdoctor@example.com")
        self.assertEqual(doctor.user.role, User.Role.DOCTOR)
        self.assertFalse(Doctor.objects.filter(user=self.existing_doctor_user).exists())
        self.assertEqual(User.objects.count(), 4)

    # -- existing account mode -------------------------------------------
    def test_existing_mode_still_supported(self):
        form = self.form(
            self.base_data(
                account_mode=ACCOUNT_MODE_EXISTING,
                user=self.existing_doctor_user.pk,
                registration_number="REG-EXIST-1",
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        doctor = form.save()
        self.assertEqual(doctor.user, self.existing_doctor_user)
        self.assertEqual(User.objects.count(), 3)

    def test_existing_mode_rejects_non_doctor_user(self):
        form = self.form(
            self.base_data(
                account_mode=ACCOUNT_MODE_EXISTING,
                user=self.patient_user.pk,
                registration_number="REG-EXIST-2",
            )
        )
        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)

    def test_existing_mode_rejects_user_with_existing_profile(self):
        profiled = User.objects.get(email="takenprofile@example.com")
        form = self.form(
            self.base_data(
                account_mode=ACCOUNT_MODE_EXISTING,
                user=profiled.pk,
                registration_number="REG-EXIST-3",
            )
        )
        self.assertFalse(form.is_valid())
        self.assertIn("user", form.errors)
        self.assertEqual(Doctor.objects.count(), 1)

    def test_tampered_account_mode_value_rejected(self):
        form = self.form(self.base_data(account_mode="hijack"))
        self.assertFalse(form.is_valid())
        self.assertIn("account_mode", form.errors)


class DoctorAdminAddPageTests(TestCase):
    """Client-level admin view tests for the dual account-mode add page."""

    def setUp(self):
        self.speciality = make_speciality("Cardiology")
        self.add_url = reverse("admin:clinic_doctor_add")
        self.admin = make_user(email="clinic-admin@example.com", role=User.Role.ADMIN)
        self.admin.is_staff = True
        self.admin.save()

    def test_add_page_renders_account_mode_fields(self):
        self.client.force_login(self.admin)
        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="account_mode"')
        self.assertContains(response, 'value="new"')
        self.assertContains(response, 'name="new_email"')
        self.assertContains(response, 'name="new_password1"')
        self.assertContains(response, 'name="new_password2"')
        self.assertContains(response, 'name="new_phone"')
        self.assertIn("js/admin/doctor_account_mode.js", response.rendered_content)

    def test_admin_post_creates_user_and_doctor_together(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            self.add_url,
            {
                "account_mode": ACCOUNT_MODE_NEW,
                "new_first_name": "Ravi",
                "new_last_name": "Kumar",
                "new_email": "dr.ravi@example.com",
                "new_phone": "9876500000",
                "new_password1": FRESH_PASSWORD,
                "new_password2": FRESH_PASSWORD,
                "registration_number": "REG-RAVI-1",
                "qualification": "MBBS, MS",
                "speciality": self.speciality.pk,
                "slot_length_minutes": "30",
                "is_accepting_appointments": "on",
                # Inline formset prefixes follow the FK related_name values.
                "availability_rules-TOTAL_FORMS": "0",
                "availability_rules-INITIAL_FORMS": "0",
                "availability_rules-MIN_NUM_FORMS": "0",
                "availability_rules-MAX_NUM_FORMS": "1000",
                "leaves-TOTAL_FORMS": "0",
                "leaves-INITIAL_FORMS": "0",
                "leaves-MIN_NUM_FORMS": "0",
                "leaves-MAX_NUM_FORMS": "1000",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        doctor = Doctor.objects.get(user__email="dr.ravi@example.com")
        self.assertEqual(doctor.user.role, User.Role.DOCTOR)
        self.assertTrue(doctor.user.check_password(FRESH_PASSWORD))
        self.assertEqual(doctor.registration_number, "REG-RAVI-1")

    def test_admin_post_with_inline_rows_saves_doctor_with_schedule(self):
        """The calendar's draft-sync path: inline rows posted with the create
        form land in the DB with ownership forced to the new doctor."""
        self.client.force_login(self.admin)
        response = self.client.post(
            self.add_url,
            {
                "account_mode": ACCOUNT_MODE_NEW,
                "new_first_name": "Priya",
                "new_last_name": "Nair",
                "new_email": "dr.priya@example.com",
                "new_phone": "9876500011",
                "new_password1": FRESH_PASSWORD,
                "new_password2": FRESH_PASSWORD,
                "registration_number": "REG-PRIYA-1",
                "qualification": "MBBS",
                "speciality": self.speciality.pk,
                "slot_length_minutes": "30",
                "is_accepting_appointments": "on",
                "availability_rules-TOTAL_FORMS": "1",
                "availability_rules-INITIAL_FORMS": "0",
                "availability_rules-MIN_NUM_FORMS": "0",
                "availability_rules-MAX_NUM_FORMS": "1000",
                "availability_rules-0-weekday": str(Weekday.MONDAY),
                "availability_rules-0-start_time": "09:00",
                "availability_rules-0-end_time": "13:00",
                "availability_rules-0-slot_length_minutes": "",
                "availability_rules-0-is_active": "on",
                "leaves-TOTAL_FORMS": "1",
                "leaves-INITIAL_FORMS": "0",
                "leaves-MIN_NUM_FORMS": "0",
                "leaves-MAX_NUM_FORMS": "1000",
                "leaves-0-start_date": "2026-12-24",
                "leaves-0-end_date": "2026-12-25",
                "leaves-0-reason": "Holiday",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        doctor = Doctor.objects.get(user__email="dr.priya@example.com")
        rule = AvailabilityRule.objects.get(doctor=doctor)
        self.assertEqual(rule.weekday, Weekday.MONDAY)
        self.assertEqual(rule.start_time, time(9, 0))
        self.assertEqual(rule.slot_length_minutes, None)  # doctor default (30)
        leave = DoctorLeave.objects.get(doctor=doctor)
        self.assertEqual(leave.reason, "Holiday")

    def test_doctors_do_not_see_the_add_doctor_page(self):
        doctor_user = make_user(
            email="staff-doctor@example.com", role=User.Role.DOCTOR, is_staff=True
        )
        self.client.force_login(doctor_user)
        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, 403)


# --------------------------------------------------------------------------
# Admin: doctor schedule calendar (JSON endpoints + template integration)
# --------------------------------------------------------------------------
def make_admin(email="schedule-admin@example.com", **kwargs):
    return make_user(email=email, role=User.Role.ADMIN, is_staff=True, **kwargs)


def make_staff_role_user(email, role, **kwargs):
    return make_user(email=email, role=role, is_staff=True, **kwargs)


class DoctorScheduleEndpointTests(TestCase):
    """JSON schedule endpoints behind the calendar widget."""

    def setUp(self):
        self.admin = make_admin()
        self.doctor = make_doctor(
            make_speciality("Cardiology"), email="cal-doctor@example.com"
        )
        self.other_doctor = make_doctor(
            make_speciality("Neurology"), email="cal-other@example.com"
        )
        self.rule = AvailabilityRule.objects.create(
            doctor=self.doctor, weekday=Weekday.MONDAY,
            start_time=time(9, 0), end_time=time(13, 0),
        )
        self.client.force_login(self.admin)
        self.events_url = reverse(
            "admin:clinic_doctor_schedule_events", args=[self.doctor.pk]
        )
        self.create_url = reverse(
            "admin:clinic_doctor_schedule_availability_create", args=[self.doctor.pk]
        )
        self.leave_create_url = reverse(
            "admin:clinic_doctor_schedule_leave_create", args=[self.doctor.pk]
        )

    # -- events ----------------------------------------------------------
    def test_events_expand_weekly_recurrence_to_concrete_dates(self):
        response = self.client.get(
            self.events_url, {"start": "2026-10-05", "end": "2026-10-18"}
        )
        payload = response.json()
        self.assertEqual(response.status_code, 200)

        mondays = [occ for occ in payload["occurrences"] if occ["weekday"] == Weekday.MONDAY]
        self.assertEqual(
            sorted(occ["date"] for occ in mondays),
            ["2026-10-05", "2026-10-12"],
        )
        first = mondays[0]
        self.assertEqual(first["rule_id"], self.rule.pk)
        self.assertEqual(first["start"], "09:00")
        self.assertEqual(first["end"], "13:00")
        self.assertTrue(first["is_active"])
        self.assertEqual(payload["leaves"], [])

    def test_events_configuration_capability_payload(self):
        response = self.client.get(
            self.events_url, {"start": "2026-10-05", "end": "2026-10-05"}
        )
        payload = response.json()
        self.assertEqual(payload["doctor"]["id"], self.doctor.pk)
        self.assertEqual(
            payload["doctor"]["default_slot_length_minutes"],
            self.doctor.slot_length_minutes,
        )
        self.assertEqual(len(payload["rules"]), 1)

    def test_events_includes_inactive_rules_marked(self):
        AvailabilityRule.objects.create(
            doctor=self.doctor, weekday=Weekday.TUESDAY,
            start_time=time(10, 0), end_time=time(12, 0), is_active=False,
        )
        response = self.client.get(
            self.events_url, {"start": "2026-10-06", "end": "2026-10-06"}
        )
        payload = response.json()
        inactive = [occ for occ in payload["occurrences"] if not occ["is_active"]]
        self.assertEqual(len(inactive), 1)
        self.assertEqual(inactive[0]["start"], "10:00")

    def test_events_include_single_and_multi_day_leaves(self):
        DoctorLeave.objects.create(
            doctor=self.doctor,
            start_date=date(2026, 11, 10), end_date=date(2026, 11, 12),
            reason="Personal leave",
        )
        DoctorLeave.objects.create(
            doctor=self.doctor,
            start_date=date(2026, 11, 16), end_date=date(2026, 11, 16),
            reason="Single day",
        )
        response = self.client.get(
            self.events_url, {"start": "2026-11-01", "end": "2026-11-30"}
        )
        payload = response.json()
        ranges = sorted((leave["start_date"], leave["end_date"]) for leave in payload["leaves"])
        self.assertEqual(
            ranges,
            [("2026-11-10", "2026-11-12"), ("2026-11-16", "2026-11-16")],
        )
        personal = next(
            leave for leave in payload["leaves"] if leave["start_date"] == "2026-11-10"
        )
        self.assertEqual(personal["reason"], "Personal leave")

    def test_events_require_valid_iso_dates(self):
        for invalid in ({"start": "not-a-date", "end": "2026-10-10"},
                        {"start": "2026-10-10"}, {}):
            with self.subTest(params=invalid):
                self.assertEqual(
                    self.client.get(self.events_url, invalid).status_code, 400
                )

    def test_events_clamp_absurd_ranges(self):
        response = self.client.get(
            self.events_url, {"start": "2026-01-01", "end": "2036-01-01"}
        )
        payload = response.json()
        start = date(2026, 1, 1)
        end = date.fromisoformat(payload["end"])
        self.assertLessEqual((end - start).days, 62)

    # -- permissions ------------------------------------------------------
    def test_anonymous_redirected_to_admin_login(self):
        client = Client()
        response = client.get(self.events_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_doctor_role_staff_user_forbidden(self):
        client = Client()
        client.force_login(make_staff_role_user("cal-dr@example.com", User.Role.DOCTOR))
        for url, method in (
            (self.events_url, "get"),
            (self.create_url, "post"),
        ):
            with self.subTest(url=url):
                response = getattr(client, method)(url)
                self.assertEqual(response.status_code, 403)

    def test_doctor_role_staff_cannot_touch_other_doctor_entries(self):
        client = Client()
        client.force_login(
            User.objects.create_user(
                email="cal-noprof@example.com", password=PASSWORD, role=User.Role.DOCTOR,
                is_staff=True,
            )
        )
        self.assertEqual(client.get(self.events_url).status_code, 403)

    def test_staff_patient_role_forbidden(self):
        client = Client()
        client.force_login(make_staff_role_user("cal-pat@example.com", User.Role.PATIENT))
        self.assertEqual(client.get(self.events_url).status_code, 403)

    # -- availability writes ----------------------------------------------
    def test_create_availability_rule_via_calendar(self):
        before = AvailabilityRule.objects.count()
        response = self.client.post(self.create_url, {
            "weekday": "1",  # Tuesday 2026-10-06
            "start_time": "09:00",
            "end_time": "13:00",
            "slot_length_minutes": "20",
            "is_active": "on",
        })
        self.assertEqual(response.status_code, 201)
        rule = AvailabilityRule.objects.get(doctor=self.doctor, weekday=Weekday.TUESDAY)
        self.assertEqual(rule.start_time, time(9, 0))
        self.assertEqual(rule.slot_length_minutes, 20)
        self.assertTrue(rule.is_active)
        self.assertEqual(AvailabilityRule.objects.count(), before + 1)

    def test_create_rejects_reversed_window(self):
        response = self.client.post(self.create_url, {
            "weekday": "1",
            "start_time": "13:00",
            "end_time": "09:00",
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            AvailabilityRule.objects.filter(
                doctor=self.doctor, weekday=Weekday.TUESDAY
            ).exists()
        )

    def test_create_rejects_overlapping_window(self):
        response = self.client.post(self.create_url, {
            "weekday": "0",
            "start_time": "12:00",
            "end_time": "14:00",
            "is_active": "on",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("start_time", response.json()["errors"])

    def test_create_rejects_invalid_weekday(self):
        response = self.client.post(self.create_url, {
            "weekday": "7",
            "start_time": "09:00",
            "end_time": "13:00",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("weekday", response.json()["errors"])

    def test_update_availability_rule(self):
        url = reverse(
            "admin:clinic_doctor_schedule_availability_update",
            args=[self.doctor.pk, self.rule.pk],
        )
        response = self.client.post(url, {
            "weekday": "0",
            "start_time": "08:30",
            "end_time": "12:30",
            "slot_length_minutes": "15",
            "is_active": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.rule.refresh_from_db()
        self.assertEqual(self.rule.start_time, time(8, 30))
        self.assertEqual(self.rule.end_time, time(12, 30))
        self.assertEqual(self.rule.slot_length_minutes, 15)

    def test_update_can_deactivate_rule(self):
        url = reverse(
            "admin:clinic_doctor_schedule_availability_update",
            args=[self.doctor.pk, self.rule.pk],
        )
        response = self.client.post(url, {
            "weekday": "0",
            "start_time": "09:00",
            "end_time": "13:00",
            # no is_active -> off
        })
        self.assertEqual(response.status_code, 200)
        self.rule.refresh_from_db()
        self.assertFalse(self.rule.is_active)

    def test_delete_availability_rule(self):
        url = reverse(
            "admin:clinic_doctor_schedule_availability_delete",
            args=[self.doctor.pk, self.rule.pk],
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            AvailabilityRule.objects.filter(pk=self.rule.pk).exists()
        )

    def test_delete_availability_never_touches_existing_slots(self):
        from appointments.models import AppointmentSlot
        slot = AppointmentSlot.objects.create(
            doctor=self.doctor, date=date(2026, 10, 12),
            start_time=time(9, 0), end_time=time(9, 20), status="OPEN",
        )
        url = reverse(
            "admin:clinic_doctor_schedule_availability_delete",
            args=[self.doctor.pk, self.rule.pk],
        )
        self.client.post(url)
        self.assertTrue(AppointmentSlot.objects.filter(pk=slot.pk).exists())

    # -- leave writes -----------------------------------------------------
    def test_create_single_day_leave(self):
        response = self.client.post(self.leave_create_url, {
            "start_date": "2026-11-10",
            "end_date": "2026-11-10",
            "reason": "Single day off",
        })
        self.assertEqual(response.status_code, 201)
        leave = DoctorLeave.objects.get(
            doctor=self.doctor, start_date=date(2026, 11, 10)
        )
        self.assertEqual(leave.end_date, date(2026, 11, 10))

    def test_create_multi_day_leave(self):
        response = self.client.post(self.leave_create_url, {
            "start_date": "2026-11-10",
            "end_date": "2026-11-12",
            "reason": "Personal leave",
        })
        self.assertEqual(response.status_code, 201)
        leave = DoctorLeave.objects.get(
            doctor=self.doctor, start_date=date(2026, 11, 10)
        )
        self.assertEqual(leave.end_date, date(2026, 11, 12))

    def test_create_rejects_reversed_leave_range(self):
        response = self.client.post(self.leave_create_url, {
            "start_date": "2026-11-12",
            "end_date": "2026-11-10",
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            DoctorLeave.objects.filter(doctor=self.doctor).exists()
        )

    def test_update_leave(self):
        leave = DoctorLeave.objects.create(
            doctor=self.doctor,
            start_date=date(2026, 11, 10), end_date=date(2026, 11, 12),
        )
        url = reverse(
            "admin:clinic_doctor_schedule_leave_update", args=[self.doctor.pk, leave.pk]
        )
        response = self.client.post(url, {
            "start_date": "2026-11-11",
            "end_date": "2026-11-13",
            "reason": "Extended leave",
        })
        self.assertEqual(response.status_code, 200)
        leave.refresh_from_db()
        self.assertEqual(leave.start_date, date(2026, 11, 11))
        self.assertEqual(leave.end_date, date(2026, 11, 13))
        self.assertEqual(leave.reason, "Extended leave")

    def test_delete_leave(self):
        leave = DoctorLeave.objects.create(
            doctor=self.doctor,
            start_date=date(2026, 11, 10), end_date=date(2026, 11, 12),
        )
        url = reverse(
            "admin:clinic_doctor_schedule_leave_delete", args=[self.doctor.pk, leave.pk]
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(DoctorLeave.objects.filter(pk=leave.pk).exists())

    # -- cross-doctor isolation -------------------------------------------
    def test_other_doctors_rule_not_reachable(self):
        other_rule = AvailabilityRule.objects.create(
            doctor=self.other_doctor, weekday=Weekday.WEDNESDAY,
            start_time=time(9, 0), end_time=time(11, 0),
        )
        for action in ("update", "delete"):
            url = reverse(
                f"admin:clinic_doctor_schedule_availability_{action}",
                args=[self.doctor.pk, other_rule.pk],
            )
            response = self.client.post(url)
            with self.subTest(action=action):
                self.assertEqual(response.status_code, 404)

    def test_other_doctors_leave_not_reachable(self):
        other_leave = DoctorLeave.objects.create(
            doctor=self.other_doctor,
            start_date=date(2026, 12, 1), end_date=date(2026, 12, 2),
        )
        for action in ("update", "delete"):
            url = reverse(
                f"admin:clinic_doctor_schedule_leave_{action}",
                args=[self.doctor.pk, other_leave.pk],
            )
            response = self.client.post(url)
            with self.subTest(action=action):
                self.assertEqual(response.status_code, 404)

    def test_events_do_not_leak_other_doctor_data(self):
        AvailabilityRule.objects.create(
            doctor=self.other_doctor, weekday=Weekday.WEDNESDAY,
            start_time=time(9, 0), end_time=time(11, 0),
        )
        response = self.client.get(
            self.events_url, {"start": "2026-10-05", "end": "2026-10-18"}
        )
        payload = response.json()
        self.assertNotIn("Wednesday", [occ["weekday_label"] for occ in payload["occurrences"]])
        self.assertNotIn(
            self.other_doctor.pk, [rule["id"] for rule in payload["rules"]]
        )

    # -- CSRF -------------------------------------------------------------
    def test_write_operations_require_csrf_token(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        response = client.post(self.create_url, {
            "weekday": "1",
            "start_time": "09:00",
            "end_time": "13:00",
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            AvailabilityRule.objects.filter(
                doctor=self.doctor, weekday=Weekday.TUESDAY
            ).exists()
        )

    # -- booking integrity -------------------------------------------------
    def test_calendar_leave_blocks_slot_generation_like_booking_validation(self):
        from django.utils import timezone
        from appointments.selectors import doctor_on_leave
        from appointments.slot_generation import generate_slots_for_doctor
        from datetime import timedelta

        # No leave yet: Monday 2026-10-05 would generate slots.
        summary = generate_slots_for_doctor(
            self.doctor, date(2026, 10, 5), date(2026, 10, 5), include_past=True
        )
        self.assertGreater(summary["created"], 0)

        response = self.client.post(self.leave_create_url, {
            "start_date": "2026-10-19",
            "end_date": "2026-10-19",
            "reason": "Leave via calendar",
        })
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            doctor_on_leave(self.doctor, date(2026, 10, 19))
        )
        summary = generate_slots_for_doctor(
            self.doctor, date(2026, 10, 19), date(2026, 10, 19), include_past=True
        )
        self.assertEqual(summary["created"], 0)

    # -- template integration ---------------------------------------------
    def test_change_page_renders_calendar_widget_with_endpoints(self):
        response = self.client.get(
            reverse("admin:clinic_doctor_change", args=[self.doctor.pk])
        )
        content = response.rendered_content
        self.assertIn('id="cc-calendar"', content)
        self.assertIn(self.events_url, content)
        self.assertIn(self.create_url, content)
        self.assertIn(self.leave_create_url, content)
        self.assertIn("csrfmiddlewaretoken", content)
        self.assertIn("doctor_schedule_calendar.js", content)
        self.assertIn("doctor_schedule_calendar.css", content)

    def test_admin_role_change_page_keeps_inline_formsets(self):
        # Inline formsets follow the administrator-only rule explicitly, so
        # role-ADMIN (non-superuser) staff get the same workflow as superusers:
        # calendar widget on the page AND inline formsets for the drafts.
        response = self.client.get(
            reverse("admin:clinic_doctor_change", args=[self.doctor.pk])
        )
        content = response.rendered_content
        self.assertIn(
            'name="availability_rules-TOTAL_FORMS"',
            content,
        )
        self.assertIn('name="leaves-TOTAL_FORMS"', content)
        self.assertIn('id="cc-calendar"', content)

    def test_superuser_change_and_add_pages_keep_inline_formsets(self):
        superuser = make_admin(email="schedule-super@example.com", is_superuser=True)
        client = self.client_class()
        client.force_login(superuser)

        # Add page: calendar in unsaved-draft mode + inline formsets for the
        # no-JavaScript fallback (both are required when JS fails).
        add_content = client.get(reverse("admin:clinic_doctor_add")).rendered_content
        self.assertIn('id="cc-calendar"', add_content)
        self.assertIn('data-unsaved="true"', add_content)
        self.assertIn(
            "/admin/clinic/doctor/0/schedule/events/",
            add_content,
        )
        self.assertIn('name="availability_rules-TOTAL_FORMS"', add_content)
        self.assertIn('name="leaves-TOTAL_FORMS"', add_content)

        # Change page: concrete endpoints + an "Advanced scheduling forms"
        # disclosure wrapping the inline formsets.
        change_content = client.get(
            reverse("admin:clinic_doctor_change", args=[self.doctor.pk])
        ).rendered_content
        self.assertIn(
            'name="availability_rules-TOTAL_FORMS"',
            change_content,
        )
        self.assertIn('data-cc-advanced', change_content)
        self.assertIn('data-unsaved="false"', change_content)
        self.assertNotIn("/admin/clinic/doctor/0/schedule/", change_content)

    def test_role_admin_pages_carry_calendar_draft_configuration(self):
        # Non-superuser role-ADMIN accounts see the same entries: the add
        # page in draft mode (JS syncs drafts into the inline formsets) and
        # the change page with concrete endpoints.
        client = self.client_class()
        client.force_login(self.admin)

        add_content = client.get(reverse("admin:clinic_doctor_add")).rendered_content
        self.assertIn('id="cc-calendar"', add_content)
        self.assertIn('data-unsaved="true"', add_content)
        self.assertIn('name="availability_rules-TOTAL_FORMS"', add_content)
        self.assertIn('name="leaves-TOTAL_FORMS"', add_content)

        change_content = client.get(
            reverse("admin:clinic_doctor_change", args=[self.doctor.pk])
        ).rendered_content
        self.assertIn('data-unsaved="false"', change_content)
        self.assertIn('data-cc-advanced', change_content)

    # -- regression guards (calendar-status failures, Oct 2026) ------------
    def test_second_create_adds_distinct_rule(self):
        """A second calendar create must add a row, never overwrite/duplicate."""
        response = self.client.post(self.create_url, {
            "weekday": "2", "start_time": "05:00", "end_time": "05:50",
            "slot_length_minutes": "", "is_active": "on",
        })
        self.assertEqual(response.status_code, 201)
        second_id = response.json()["rule"]["id"]
        response = self.client.post(self.create_url, {
            "weekday": "5", "start_time": "06:00", "end_time": "07:00",
            "slot_length_minutes": "", "is_active": "on",
        })
        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.json()["rule"]["id"], second_id)
        self.assertEqual(
            AvailabilityRule.objects.filter(doctor=self.doctor).count(), 3
        )

    def test_update_edits_existing_row_without_creating_duplicate(self):
        response = self.client.post(
            reverse("admin:clinic_doctor_schedule_availability_update",
                    args=[self.doctor.pk, self.rule.pk]),
            {
            "weekday": "5", "start_time": "08:30", "end_time": "15:30",
            "slot_length_minutes": "20", "is_active": "on",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rule"]["id"], self.rule.pk)
        before = self.rule
        before.refresh_from_db()
        self.assertEqual(before.start_time, time(8, 30))
        self.assertEqual(before.weekday, Weekday.SATURDAY)
        self.assertEqual(
            AvailabilityRule.objects.filter(doctor=self.doctor).count(), 1
        )

    def test_events_payload_matches_renderer_contract(self):
        """The client renderer is driven only by these keys; keep them stable."""
        response = self.client.get(
            self.events_url, {"start": "2026-10-19", "end": "2026-10-25"}
        )
        payload = response.json()
        self.assertEqual(response.status_code, 200)
        for key in ("doctor", "start", "end", "occurrences", "rules", "leaves"):
            self.assertIn(key, payload)
        self.assertIn("name", payload["doctor"])
        self.assertIn(
            "default_slot_length_minutes", payload["doctor"]
        )
        self.assertGreater(len(payload["occurrences"]), 0)
        occurrence = payload["occurrences"][0]
        for key in (
            "rule_id", "date", "weekday", "start", "end",
            "slot_length_minutes", "effective_slot_length_minutes", "is_active",
        ):
            self.assertIn(key, occurrence)
        rule = payload["rules"][0]
        self.assertIn("weekday_label", rule)

    def test_change_page_dom_hooks_needed_by_calendar_js(self):
        """The JS selects these hooks; missing any of them breaks the widget
        (the calendar grid never renders and the inline formsets stay open)."""
        response = self.client.get(
            reverse("admin:clinic_doctor_change", args=[self.doctor.pk])
        )
        content = response.rendered_content
        js_hooks = [
            'id="cc-calendar"',
            "data-events-url",
            "data-availability-create-url",
            "data-leave-create-url",
            "data-board",
            "data-range-label",
            "data-status",
            "data-spinner",
            "data-csrf",
            'id="cc-menu"',
            "data-menu-date-label",
            'id="cc-availability-form"',
            "data-availability-repeat-label",
            'id="cc-availability-weekday"',
            'id="cc-availability-start"',
            'id="cc-availability-end"',
            'id="cc-availability-slot"',
            'id="cc-availability-active"',
            'id="cc-leave-form"',
            'id="cc-leave-start"',
            'id="cc-leave-end"',
            'id="cc-leave-reason"',
            'id="cc-details"',
            'id="cc-details-title"',
            "data-details-list",
            "data-details-note",
            'id="cc-confirm"',
            "data-confirm-text",
            "data-menu=\"availability\"",
            "data-menu=\"leave\"",
            "data-cmd=\"save\"",
            "data-details=\"edit\"",
            "data-details=\"toggle\"",
            "data-details=\"delete\"",
            "data-confirm=\"yes\"",
            "data-confirm=\"no\"",
        ]
        for hook in js_hooks:
            with self.subTest(hook=hook):
                self.assertIn(hook, content)
        self.assertIn(
            "/static/js/admin/doctor_schedule_calendar.js", content
        )
        self.assertIn(
            "/static/css/admin/doctor_schedule_calendar.css", content
        )


class ScheduleHubTests(TestCase):
    """Availability Rules / Doctor Leave entries land on one calendar hub.

    The hub reuses the DoctorAdmin scheduling endpoints through the "/0/"
    sentinel URLs; administrators get the calendar, doctors keep their
    own-scoped table page (the hub selects arbitrary doctors).
    """

    def setUp(self):
        self.admin = make_admin()
        self.doctor = make_doctor(
            make_speciality("Cardiology"), email="hub-doctor@example.com"
        )
        self.availability_hub_url = reverse("admin:clinic_availabilityrule_schedule_hub")
        self.leave_hub_url = reverse("admin:clinic_doctorleave_schedule_hub")
        self.availability_changelist_url = reverse("admin:clinic_availabilityrule_changelist")
        self.leave_changelist_url = reverse("admin:clinic_doctorleave_changelist")
        self.client.force_login(self.admin)

    @staticmethod
    def sentinel_urls():
        return (
            "/admin/clinic/doctor/0/schedule/events/",
            "/admin/clinic/doctor/0/schedule/availability/create/",
            "/admin/clinic/doctor/0/schedule/leave/create/",
        )

    # -- redirects ---------------------------------------------------------
    def test_availabilityrule_changelist_redirects_admin_to_hub(self):
        response = self.client.get(self.availability_changelist_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.availability_hub_url)

    def test_doctorleave_changelist_redirects_admin_to_hub(self):
        response = self.client.get(self.leave_changelist_url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], self.leave_hub_url)

    def test_explicit_table_param_keeps_the_classical_changelist(self):
        # "?o=1" is a valid changelist ordering param; custom keys would be
        # rejected by the admin's query-string validation (?e=1 redirect).
        for url in (self.availability_changelist_url, self.leave_changelist_url):
            response = self.client.get(url + "?o=1")
            self.assertEqual(response.status_code, 200)
            self.assertNotIn('id="cc-calendar"', response.rendered_content)

    # -- hub rendering ------------------------------------------------------
    def test_availabilityrule_hub_renders_calendar_and_doctor_selector(self):
        response = self.client.get(self.availability_hub_url)
        content = response.rendered_content
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="cc-calendar"', content)
        self.assertIn('data-mode="availability"', content)
        self.assertIn('data-unsaved="false"', content)
        for sentinel in self.sentinel_urls():
            self.assertIn(sentinel, content)
        self.assertIn('data-doctor-select', content)
        self.assertIn('id="cc-doctor-select"', content)
        self.assertIn("hub-doctor@example.com", content)  # doctor option label
        self.assertIn("?o=1", content)  # fallback link
        self.assertIn("doctor_schedule_calendar.js", content)
        self.assertIn("doctor_schedule_calendar.css", content)

    def test_doctorleave_hub_renders_calendar_with_leave_mode(self):
        response = self.client.get(self.leave_hub_url)
        self.assertEqual(response.status_code, 200)
        content = response.rendered_content
        self.assertIn('data-mode="leave"', content)
        self.assertIn('data-doctor-select', content)

    def test_hub_preselects_doctor_from_query_param(self):
        response = self.client.get(self.availability_hub_url + f"?doctor={self.doctor.pk}")
        content = response.rendered_content
        self.assertEqual(response.status_code, 200)
        self.assertIn(f'data-doctor="{self.doctor.pk}"', content)
        option = ['<option value="%d" selected>' % self.doctor.pk]
        for marker in option:
            self.assertIn(marker, content)
        self.assertIn("data-cc-doctor-picker", content)
        # A preselected hub shows no placeholder option.
        self.assertNotIn("Choose a doctor to view their schedule", content)

    def test_hub_without_doctor_shows_placeholder_option(self):
        for url in (self.availability_hub_url, self.leave_hub_url):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            content = response.rendered_content
            self.assertIn("Choose a doctor to view their schedule", content)
            self.assertIn('<option value="" disabled selected>', content)

    # -- doctor-role access --------------------------------------------------
    def test_hub_rejects_doctor_role_with_403(self):
        doctor_user = make_staff_role_user("hub-self@example.com", User.Role.DOCTOR)
        client = self.client_class()
        client.force_login(doctor_user)
        for url in (self.availability_hub_url, self.leave_hub_url):
            response = client.get(url)
            self.assertEqual(response.status_code, 403)

    def test_doctor_role_keeps_the_self_scoped_changelist_table(self):
        doctor_user = make_staff_role_user("hub-self@example.com", User.Role.DOCTOR)
        self.doctor.user = doctor_user
        self.doctor.save()
        AvailabilityRule.objects.create(
            doctor=self.doctor, weekday=Weekday.MONDAY,
            start_time=time(9, 0), end_time=time(13, 0),
        )
        client = self.client_class()
        client.force_login(doctor_user)
        response = client.get(self.availability_changelist_url)
        self.assertEqual(response.status_code, 200)
        content = response.rendered_content
        self.assertIn("hub-self@example.com", content)  # scoped row is listed
        self.assertNotIn('id="cc-calendar"', content)
        self.assertNotIn('data-doctor-select', content)
