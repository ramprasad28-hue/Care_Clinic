"""Tests for the accounts app: user model, registration, auth, and RBAC.

Runnable via either:
    python manage.py test
    pytest
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.db import IntegrityError
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views import View

from .forms import PatientRegistrationForm
from .permissions import RoleRequiredMixin, role_required

User = get_user_model()

PASSWORD = "S3cret-pass!"


def make_user(email="user@example.com", role=User.Role.PATIENT, **kwargs):
    return User.objects.create_user(email=email, password=PASSWORD, role=role, **kwargs)


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------
class UserModelTests(TestCase):
    def test_create_user_with_email(self):
        user = make_user()
        self.assertEqual(user.email, "user@example.com")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_role_defaults_to_patient(self):
        user = make_user()
        self.assertEqual(user.role, User.Role.PATIENT)
        self.assertTrue(user.is_patient)

    def test_email_is_normalised(self):
        user = make_user(email="MixedCase@Example.COM")
        self.assertEqual(user.email, "MixedCase@example.com")

    def test_email_must_be_unique(self):
        make_user()
        with self.assertRaises(IntegrityError):
            make_user()

    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password=PASSWORD)

    def test_str_returns_email(self):
        self.assertEqual(str(make_user()), "user@example.com")

    def test_role_choices_are_stable(self):
        self.assertEqual(
            set(User.Role.values),
            {"PATIENT", "DOCTOR", "RECEPTIONIST", "ADMIN"},
        )

    def test_has_role(self):
        doctor = make_user(email="d@example.com", role=User.Role.DOCTOR)
        self.assertTrue(doctor.has_role(User.Role.DOCTOR))
        self.assertFalse(doctor.has_role(User.Role.PATIENT))

    def test_superuser_has_every_role(self):
        admin = User.objects.create_superuser(email="a@example.com", password=PASSWORD)
        self.assertTrue(admin.has_role(User.Role.PATIENT, User.Role.DOCTOR))
        self.assertEqual(admin.role, User.Role.ADMIN)


class SuperuserTests(TestCase):
    def test_create_superuser(self):
        admin = User.objects.create_superuser(email="admin@example.com", password=PASSWORD)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertEqual(admin.role, User.Role.ADMIN)

    def test_create_superuser_rejects_non_staff_flag(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="bad@example.com", password=PASSWORD, is_staff=False
            )


# --------------------------------------------------------------------------
# Registration form
# --------------------------------------------------------------------------
class RegistrationFormTests(TestCase):
    def valid_data(self, **overrides):
        data = {
            "first_name": "Asha",
            "last_name": "Rao",
            "email": "asha@example.com",
            "phone": "9876543210",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_valid_form_saves_patient(self):
        form = PatientRegistrationForm(data=self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.role, User.Role.PATIENT)
        self.assertTrue(user.check_password(PASSWORD))

    def test_role_is_not_a_form_field(self):
        form = PatientRegistrationForm()
        self.assertNotIn("role", form.fields)

    def test_submitted_role_is_ignored(self):
        form = PatientRegistrationForm(data=self.valid_data(role="ADMIN"))
        self.assertTrue(form.is_valid(), form.errors)
        user = form.save()
        self.assertEqual(user.role, User.Role.PATIENT)

    def test_duplicate_email_rejected(self):
        make_user(email="asha@example.com")
        form = PatientRegistrationForm(data=self.valid_data())
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_weak_password_rejected(self):
        form = PatientRegistrationForm(data=self.valid_data(password1="123", password2="123"))
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


# --------------------------------------------------------------------------
# Registration view
# --------------------------------------------------------------------------
class RegistrationViewTests(TestCase):
    url = reverse("accounts:register")

    def valid_data(self, **overrides):
        data = {
            "first_name": "Asha",
            "last_name": "Rao",
            "email": "asha@example.com",
            "phone": "9876543210",
            "password1": PASSWORD,
            "password2": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_get_renders(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "patients only")

    def test_post_creates_patient_and_logs_in(self):
        response = self.client.post(self.url, self.valid_data())
        self.assertRedirects(response, reverse("home"))
        user = User.objects.get(email="asha@example.com")
        self.assertEqual(user.role, User.Role.PATIENT)
        # Session now holds the authenticated user.
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_role_in_post_ignored(self):
        self.client.post(self.url, self.valid_data(role="ADMIN"))
        self.assertEqual(User.objects.get(email="asha@example.com").role, User.Role.PATIENT)

    def test_authenticated_user_redirected(self):
        self.client.force_login(make_user())
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("home"))


# --------------------------------------------------------------------------
# Auth flows
# --------------------------------------------------------------------------
class AuthFlowTests(TestCase):
    def test_login_with_email(self):
        make_user(email="login@example.com")
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "login@example.com", "password": PASSWORD},
        )
        self.assertRedirects(response, reverse("home"))

    def test_inactive_user_cannot_login(self):
        make_user(email="off@example.com", is_active=False)
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "off@example.com", "password": PASSWORD},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_post(self):
        self.client.force_login(make_user())
        self.assertEqual(self.client.get(reverse("accounts:logout")).status_code, 405)
        response = self.client.post(reverse("accounts:logout"))
        self.assertRedirects(response, reverse("home"))

    def test_password_reset_end_to_end(self):
        user = make_user(email="reset@example.com")
        response = self.client.post(
            reverse("accounts:password_reset"), {"email": user.email}
        )
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        confirm_url = reverse(
            "accounts:password_reset_confirm", kwargs={"uidb64": uid, "token": token}
        )
        # First GET validates the token and redirects to the set-password URL.
        response = self.client.get(confirm_url)
        self.assertEqual(response.status_code, 302)
        set_url = response.url
        response = self.client.post(
            set_url, {"new_password1": "New-pass-456", "new_password2": "New-pass-456"}
        )
        self.assertRedirects(response, reverse("accounts:password_reset_complete"))
        user.refresh_from_db()
        self.assertTrue(user.check_password("New-pass-456"))


# --------------------------------------------------------------------------
# RBAC primitives
# --------------------------------------------------------------------------
class RoleRequiredDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        @role_required(User.Role.DOCTOR)
        def protected(request):
            return HttpResponse("ok")

        self.view = protected

    def test_anonymous_redirected_to_login(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        response = self.view(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

    def test_wrong_role_forbidden(self):
        request = self.factory.get("/")
        request.user = make_user(role=User.Role.PATIENT)
        with self.assertRaises(PermissionDenied):
            self.view(request)

    def test_allowed_role_ok(self):
        request = self.factory.get("/")
        request.user = make_user(email="d@example.com", role=User.Role.DOCTOR)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)

    def test_superuser_allowed(self):
        request = self.factory.get("/")
        request.user = User.objects.create_superuser(email="root@example.com", password=PASSWORD)
        self.assertEqual(self.view(request).status_code, 200)


class RoleRequiredMixinTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        class DoctorOnly(RoleRequiredMixin, View):
            allowed_roles = (User.Role.DOCTOR,)

            def get(self, request):
                return HttpResponse("ok")

        self.view = DoctorOnly.as_view()

    def test_anonymous_redirected(self):
        request = self.factory.get("/")
        request.user = AnonymousUser()
        request.session = {}
        response = self.view(request)
        self.assertEqual(response.status_code, 302)

    def test_wrong_role_forbidden(self):
        request = self.factory.get("/")
        request.user = make_user(role=User.Role.PATIENT)
        with self.assertRaises(PermissionDenied):
            self.view(request)

    def test_allowed_role_ok(self):
        request = self.factory.get("/")
        request.user = make_user(email="d@example.com", role=User.Role.DOCTOR)
        response = self.view(request)
        self.assertEqual(response.status_code, 200)


# --------------------------------------------------------------------------
# sync_roles command
# --------------------------------------------------------------------------
class SyncRolesCommandTests(TestCase):
    def test_creates_role_groups(self):
        call_command("sync_roles")
        self.assertEqual(Group.objects.count(), 4)
        self.assertTrue(Group.objects.filter(name="Administrator").exists())

    def test_admin_group_has_user_permissions(self):
        call_command("sync_roles")
        admin_group = Group.objects.get(name="Administrator")
        codenames = set(admin_group.permissions.values_list("codename", flat=True))
        self.assertIn("change_user", codenames)

    def test_membership_reconciled_with_role(self):
        doctor = make_user(email="d@example.com", role=User.Role.DOCTOR)
        call_command("sync_roles")
        self.assertIn(Group.objects.get(name="Doctor"), doctor.groups.all())

    def test_idempotent(self):
        call_command("sync_roles")
        call_command("sync_roles")
        self.assertEqual(Group.objects.count(), 4)

    def test_dry_run_changes_nothing(self):
        call_command("sync_roles", "--dry-run")
        self.assertEqual(Group.objects.count(), 0)
