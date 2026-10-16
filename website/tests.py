"""Tests for the public website (home, specialities, doctors)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clinic.models import AvailabilityRule, Doctor, Speciality, Weekday

User = get_user_model()


def make_speciality(name="Cardiology", is_active=True):
    return Speciality.objects.create(name=name, is_active=is_active)


def make_doctor(
    speciality,
    email,
    first_name="Doc",
    last_name="Smith",
    is_accepting=True,
    user_active=True,
    **kwargs,
):
    user = User.objects.create_user(
        email=email,
        password="S3cret-pass!",
        role=User.Role.DOCTOR,
        is_active=user_active,
        first_name=first_name,
        last_name=last_name,
    )
    return Doctor.objects.create(
        user=user,
        speciality=speciality,
        registration_number=f"REG-{email}",
        qualification=kwargs.pop("qualification", "MBBS"),
        is_accepting_appointments=is_accepting,
        **kwargs,
    )


class HomePageTests(TestCase):
    def test_home_ok_for_anonymous(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_home_lists_active_speciality(self):
        make_speciality("Cardiology")
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Cardiology")


class SpecialityPageTests(TestCase):
    def test_list_shows_only_active(self):
        make_speciality("Cardiology", is_active=True)
        make_speciality("Dermatology", is_active=False)
        response = self.client.get(reverse("speciality_list"))
        self.assertContains(response, "Cardiology")
        self.assertNotContains(response, "Dermatology")

    def test_detail_active_ok(self):
        spec = make_speciality("Cardiology")
        response = self.client.get(spec.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cardiology")

    def test_detail_inactive_is_404(self):
        spec = make_speciality("Dermatology", is_active=False)
        self.assertEqual(self.client.get(spec.get_absolute_url()).status_code, 404)

    def test_detail_unknown_is_404(self):
        self.assertEqual(
            self.client.get(reverse("speciality_detail", kwargs={"slug": "nope"})).status_code,
            404,
        )


class DoctorPageTests(TestCase):
    def setUp(self):
        self.cardio = make_speciality("Cardiology")
        self.derma = make_speciality("Dermatology")
        self.accepting = make_doctor(
            self.cardio, "a@example.com", first_name="Alice", last_name="Anderson"
        )
        self.not_accepting = make_doctor(
            self.derma, "b@example.com", first_name="Bob", last_name="Brown",
            is_accepting=False,
        )

    def test_list_shows_only_accepting(self):
        response = self.client.get(reverse("doctor_list"))
        self.assertContains(response, "Alice Anderson")
        self.assertNotContains(response, "Bob Brown")

    def test_list_shows_doctor_name(self):
        response = self.client.get(reverse("doctor_list"))
        self.assertContains(response, self.accepting.user.get_full_name())

    def test_filter_by_speciality(self):
        other_cardio = make_doctor(
            self.cardio, "c@example.com", first_name="Carol", last_name="Clark"
        )
        response = self.client.get(reverse("doctor_list"), {"speciality": self.cardio.slug})
        self.assertContains(response, other_cardio.user.get_full_name())
        self.assertNotContains(response, "Bob Brown")

    def test_detail_accepting_ok(self):
        response = self.client.get(self.accepting.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_detail_non_accepting_is_404(self):
        self.assertEqual(
            self.client.get(self.not_accepting.get_absolute_url()).status_code, 404
        )

    def test_detail_unknown_is_404(self):
        self.assertEqual(
            self.client.get(reverse("doctor_detail", kwargs={"slug": "nope"})).status_code,
            404,
        )

    def test_inactive_user_hidden(self):
        hidden = make_doctor(
            self.cardio, "d@example.com", first_name="Dan", last_name="Davis",
            user_active=False,
        )
        self.assertEqual(self.client.get(hidden.get_absolute_url()).status_code, 404)


class DoctorDetailAvailabilityTests(TestCase):
    def test_detail_renders_availability(self):
        spec = make_speciality("Cardiology")
        doctor = make_doctor(spec, "a@example.com", first_name="Alice", last_name="Anderson")
        AvailabilityRule.objects.create(
            doctor=doctor,
            weekday=Weekday.MONDAY,
            start_time="09:00",
            end_time="11:00",
            slot_length_minutes=15,
        )
        response = self.client.get(doctor.get_absolute_url())
        self.assertContains(response, "Monday")
        self.assertContains(response, "15 min")
