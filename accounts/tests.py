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
import re

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


# --------------------------------------------------------------------------
# F-06 security: Django UserAdmin privilege-escalation boundary
# --------------------------------------------------------------------------
class UserAdminSecurityTests(TestCase):
    """Verify the privilege-escalation guards of the custom ``UserAdmin``.

    Security boundaries under test (accounts/admin.py):

    1. User-add is permission-gated: a non-superuser may create users only
       while holding ``accounts.add_user`` (the "Administrator" role group
       receives it via ``sync_roles``, per ADR-012 delegated provisioning).
       Staff status alone — with or without ``change_user`` — is denied, and
       a denied POST creates no User row.
    2. Non-superusers cannot grant ``is_superuser`` / ``is_staff`` / the
       Administrator ``role`` / ``groups`` / ``user_permissions`` to any
       user through the change form — posted values are re-asserted away
       server-side around Django's save, and existing protected values and
       relations are never erased.
    3. On delegated (non-superuser) add, ``is_staff``/``is_superuser`` are
       forced off and the Administrator role is not selectable; no forged
       add POST can create a privileged account.
    4. Superuser rows are invisible to non-superusers: excluded from the
       changelist, and direct admin URLs (change/delete/history) answer a
       hidden superuser ID exactly like a nonexistent User ID — same HTTP
       status, same redirect target, same message template — leaking no
       distinguishable information, and leaving the protected account
       unchanged.
    5. A non-superuser cannot delete their own account (self-protection).
    6. Positive controls: real superusers retain full UserAdmin ability,
       including flag-granting and account creation — the guards must not
       weaken superuser functionality.

    Response codes are asserted exactly (403/404/302) — never ``!= 200``
    — and every denial test reloads the affected row from the database to
    prove the attempt had no effect.
    """

    @staticmethod
    def _model_permission(codename):
        from django.contrib.auth.models import Permission

        return Permission.objects.get(
            content_type__app_label="accounts", codename=codename
        )

    def setUp(self):
        self.the_superuser = make_user(
            email="root@example.com",
            role=User.Role.ADMIN,
            is_superuser=True,
            is_staff=True,
        )
        self.client_user = make_user(email="victim@example.com")
        self.view_admin = make_user(
            email="sysadmin@example.com", role=User.Role.ADMIN
        )
        self.view_admin.is_staff = True
        self.view_admin.save(update_fields=["is_staff"])

    def _grant(self, user, *codenames):
        for codename in codenames:
            user.user_permissions.add(self._model_permission(codename))

    def _why_not_saved(self, response):
        """Diagnostic message exposing admin form errors for failed saves."""
        detail = ""
        html = getattr(response, "content", b"") or b""
        if b"id=id_date_joined_error" in html:
            detail = "date_joined missing"
        ctx = getattr(response, "context", None)
        if ctx is not None:
            try:
                errors = ctx["errors"]
                detail = f"form errors: {errors}"
            except (AttributeError, KeyError):
                pass
        if not detail:
            return f"expected 302 after saving; got {response.status_code}"
        return f"expected 302 after saving; got {response.status_code}; {detail}"

    def _change_payload(self, target, **overrides):
        """A form-valid change submission for ``target``.

        Only fields the admin change form actually renders are posted.
        ModelAdmin renders DateTimeFields with ``AdminSplitDateTime``, so
        the important dates are submitted as ``<name>_0`` (date) and
        ``<name>_1`` (time) pairs.
        """
        data = {
            # Declared form field on Django's UserChangeForm; the model has
            # no username column, so it only flows through form validation.
            "username": target.email,
            "email": target.email,
            "first_name": target.first_name,
            "last_name": target.last_name,
            "phone": target.phone,
            "is_active": "on" if target.is_active else "0",
            "date_joined_0": target.date_joined.strftime("%Y-%m-%d"),
            "date_joined_1": target.date_joined.strftime("%H:%M:%S"),
        }
        if target.last_login is not None:
            data["last_login_0"] = target.last_login.strftime("%Y-%m-%d")
            data["last_login_1"] = target.last_login.strftime("%H:%M:%S")
        data.update(overrides)
        return data

    # ---------------- B. User-add permission boundary --------------------
    def test_add_view_denied_without_add_user_permission(self):
        """A non-superuser staff user with no accounts permissions must be
        denied the add view with HTTP 403 — staff status alone is not a grant
        (policy gate lives in UserAdmin.has_add_permission).
        """
        self.client.force_login(self.view_admin)
        self.assertFalse(self.view_admin.has_perm("accounts.add_user"))
        response = self.client.get(reverse("admin:accounts_user_add"))
        self.assertEqual(
            response.status_code,
            403,
            "add view must be permission-gated for non-superusers",
        )

    def test_add_view_denied_with_change_permission_but_no_add_permission(self):
        """The decisive Option-A boundary: a staff user holding
        ``change_user`` but NOT ``add_user`` satisfies the request-level
        change check, so only our own add gate can deny the add view.
        """
        self._grant(self.view_admin, "change_user")
        self.assertFalse(self.view_admin.has_perm("accounts.add_user"))
        self.client.force_login(self.view_admin)
        response = self.client.get(reverse("admin:accounts_user_add"))
        self.assertEqual(
            response.status_code,
            403,
            "add view must require accounts.add_user even when the user "
            "has the change permission",
        )

    def test_add_post_cannot_create_or_grant_privileges(self):
        """A POST to the add URL from a staff user without ``add_user``
        permission must be denied and must not create any User row —
        regardless of the submitted flag values.
        """
        self._grant(self.view_admin, "change_user")
        self.client.force_login(self.view_admin)
        before = User.objects.count()
        response = self.client.post(
            reverse("admin:accounts_user_add"),
            {
                "username": "attacker@example.com",
                "email": "attacker@example.com",
                "password1": PASSWORD,
                "password2": PASSWORD,
                "role": User.Role.ADMIN,
                "is_staff": "on",
                "is_superuser": "on",
            },
        )
        self.assertEqual(
            response.status_code,
            403,
            "add must be permission-gated for non-superusers",
        )
        self.assertEqual(
            User.objects.count(),
            before,
            "a denied add attempt must not create a User record",
        )
        self.assertFalse(
            User.objects.filter(email="attacker@example.com").exists()
        )

    def test_add_view_denied_with_add_permission_but_no_change_permission(self):
        """Permission combination: ``add_user`` without ``change_user``.
        BaseUserAdmin refuses the add flow for users who cannot change
        users (django/contrib/auth/admin.py `_add_view`) — a denied POST
        must also create no row.
        """
        self._grant(self.view_admin, "add_user")
        self.assertFalse(self.view_admin.has_perm("accounts.change_user"))
        self.client.force_login(self.view_admin)
        before = User.objects.count()
        for method, data in [
            ("get", None),
            (
                "post",
                {
                    "email": "nochange@example.com",
                    "password1": PASSWORD,
                    "password2": PASSWORD,
                    "role": User.Role.PATIENT,
                    "is_staff": "on",
                    "is_superuser": "on",
                },
            ),
        ]:
            if method == "get":
                response = self.client.get(reverse("admin:accounts_user_add"))
            else:
                response = self.client.post(reverse("admin:accounts_user_add"), data)
            self.assertEqual(
                response.status_code,
                403,
                f"add view with change-less add_user must deny ({method})",
            )
        self.assertEqual(
            User.objects.count(),
            before,
            "denied change-less delegated add must not create a row",
        )

    def test_delegated_admin_can_add_ordinary_account(self):
        """Positive delegated control: an admin holding add_user+change_user
        can create an ordinary account; forged is_staff/is_superuser values
        are forced off server-side and the chosen non-privileged role sticks.
        """
        self._grant(self.view_admin, "add_user", "change_user")
        self.client.force_login(self.view_admin)
        response = self.client.get(reverse("admin:accounts_user_add"))
        self.assertEqual(response.status_code, 200)
        before = User.objects.count()
        response = self.client.post(
            reverse("admin:accounts_user_add"),
            {
                "email": "delegated@example.com",
                "password1": PASSWORD,
                "password2": PASSWORD,
                "role": User.Role.DOCTOR,
                "is_staff": "on",  # forged flag on an otherwise valid form
                "is_superuser": "on",  # forged flag
            },
        )
        self.assertEqual(response.status_code, 302)
        created = User.objects.filter(email="delegated@example.com").first()
        self.assertIsNotNone(created, "delegated add must create the account")
        self.assertEqual(User.objects.count(), before + 1)
        self.assertTrue(
            created.check_password(PASSWORD), "delegated add must set password"
        )
        self.assertEqual(created.role, User.Role.DOCTOR)
        self.assertFalse(
            created.is_staff,
            "delegated add must not be able to grant staff status",
        )
        self.assertFalse(
            created.is_superuser,
            "delegated add must not be able to grant superuser",
        )

    def test_delegated_add_cannot_provision_admin_role(self):
        """On the delegated add form no Administrator role is selectable;
        a forged role=ADMIN value is rejected before any row is created.
        """
        self._grant(self.view_admin, "add_user", "change_user")
        self.client.force_login(self.view_admin)
        before = User.objects.count()
        response = self.client.post(
            reverse("admin:accounts_user_add"),
            {
                "email": "wannabe-admin@example.com",
                "password1": PASSWORD,
                "password2": PASSWORD,
                "role": User.Role.ADMIN,  # forged privileged role
                "is_staff": "on",
                "is_superuser": "on",
            },
        )
        self.assertEqual(
            User.objects.count(),
            before,
            "a forged Administrator-role add must not create a User row",
        )
        self.assertFalse(
            User.objects.filter(email="wannabe-admin@example.com").exists()
        )
        self.assertNotEqual(response.status_code, 302)

    # ---------------- C. Elevated-field protection -----------------------
    def test_change_post_cannot_grant_privileges(self):
        """POSTing privileged field values through another user's change
        form as a non-superuser must not persist any of them.

        The submission itself is form-valid (the fields are rendered for
        the requester and attacked values ride on disabled inputs), so any
        protection observed here is server-side neutralisation — not a
        validation failure being mistaken for security.
        """
        escalate_group, _ = Group.objects.get_or_create(name="EscalateGroup")
        escalate_group.permissions.add(self._model_permission("change_user"))
        self._grant(self.view_admin, "change_user", "view_user")
        target = self.client_user
        # Give the target a pre-existing, harmless permission so the test can
        # prove an attack POST (a) cannot grant additional/privileged
        # permissions and (b) cannot wipe the existing assignment.
        initial_permission = self._model_permission("view_user")
        target.user_permissions.add(initial_permission)
        self.client.force_login(self.view_admin)
        response = self.client.post(
            reverse("admin:accounts_user_change", args=(target.pk,)),
            self._change_payload(
                target,
                # legitimate non-protected edit, must persist
                first_name="Renamed",
                # attack: escalation via every protected field
                is_superuser="on",
                is_staff="on",
                role=User.Role.ADMIN,
                groups=[escalate_group.pk],
                user_permissions=[self._model_permission("change_user")],
            ),
        )
        self.assertEqual(
            response.status_code,
            302,
            "the underlying change form should save cleanly; escalation "
            "must be neutralised server-side, not via validation errors "
            f"({self._why_not_saved(response)})",
        )
        target.refresh_from_db()
        self.assertEqual(
            target.first_name,
            "Renamed",
            "legitimate contact-name edit must persist alongside the attack",
        )
        self.assertFalse(target.is_superuser, "is_superuser grant persisted!")
        self.assertFalse(target.is_staff, "is_staff grant persisted!")
        self.assertEqual(
            target.role,
            User.Role.PATIENT,
            "privileged role change persisted!",
        )
        self.assertFalse(
            target.groups.exists(),
            "group assignment persisted!",
        )
        self.assertEqual(
            list(target.user_permissions.values_list("pk", flat=True)),
            [initial_permission.pk],
            "existing permission was replaced by the attack payload!",
        )

    def _attempt_escalation(self, **attack):
        """Submit a form-valid change POST carrying a legitimate contact-file
        edit plus the given attack values for a protected field. Reloads the
        target and returns it, after proving the legitimate edit persisted.
        """
        self._grant(self.view_admin, "change_user")
        target = self.client_user
        self.client.force_login(self.view_admin)
        response = self.client.post(
            reverse("admin:accounts_user_change", args=(target.pk,)),
            self._change_payload(target, first_name="Renamed", **attack),
        )
        self.assertEqual(
            response.status_code,
            302,
            "the underlying change form should save cleanly; escalation "
            f"must be neutralised server-side ({self._why_not_saved(response)})",
        )
        target.refresh_from_db()
        self.assertEqual(
            target.first_name, "Renamed", "legitimate edit must still persist"
        )
        return target

    def test_change_post_cannot_grant_superuser_flag(self):
        target = self._attempt_escalation(is_superuser="on")
        self.assertFalse(target.is_superuser, "is_superuser grant persisted!")

    def test_change_post_cannot_grant_staff_flag(self):
        target = self._attempt_escalation(is_staff="on")
        self.assertFalse(target.is_staff, "is_staff grant persisted!")

    def test_change_post_cannot_change_role_to_admin(self):
        target = self._attempt_escalation(role=User.Role.ADMIN)
        self.assertEqual(target.role, User.Role.PATIENT, "role change persisted!")

    def test_change_post_cannot_assign_foreign_group(self):
        escalate_group, _ = Group.objects.get_or_create(name="EscalateGroup")
        target = self._attempt_escalation(groups=[escalate_group.pk])
        self.assertFalse(target.groups.exists(), "group assignment persisted!")

    def test_change_post_cannot_assign_user_permissions(self):
        target = self.client_user
        initial_permission = self._model_permission("view_user")
        target.user_permissions.add(initial_permission)
        attacked = self._attempt_escalation(
            user_permissions=[self._model_permission("change_user")]
        )
        self.assertEqual(
            list(attacked.user_permissions.values_list("pk", flat=True)),
            [initial_permission.pk],
            "existing permissions were replaced by the attack payload!",
        )

    # ---------------- D. Superuser protection ---------------------------
    def _assert_superuser_hidden(self):
        self.assertTrue(
            User.objects.filter(
                email=self.the_superuser.email, is_superuser=True
            ).exists()
        )

    def _assert_equivocal_response(self, viewname, method="get", data=None):
        """A hidden-superuser admin URL must be externally indistinguishable
        from the same URL for a nonexistent User ID: equal HTTP status, equal
        redirect target, and an identical message template (only the quoted
        ID differs). Nothing about the protected account may be revealed or
        changed.
        """
        missing_pk = User.objects.order_by("-pk").first().pk + 1
        hidden = reverse(viewname, args=(self.the_superuser.pk,))
        missing = reverse(viewname, args=(missing_pk,))
        if method == "get":
            response_hidden = self.client.get(hidden)
        else:
            response_hidden = self.client.post(hidden, data or {})
        followed_hidden = self.client.get(response_hidden.get("Location"))
        if method == "get":
            response_missing = self.client.get(missing)
        else:
            response_missing = self.client.post(missing, data or {})
        followed_missing = self.client.get(response_missing.get("Location"))
        self.assertEqual(
            response_hidden.status_code,
            response_missing.status_code,
            "hidden superuser and missing user must answer identically",
        )
        self.assertEqual(
            response_hidden.get("Location"),
            response_missing.get("Location"),
            "redirect targets must be identical",
        )
        followed_hidden = self.client.get(response_hidden.get("Location"))
        followed_missing = self.client.get(response_missing.get("Location"))
        self.assertEqual(
            followed_hidden.status_code, followed_missing.status_code
        )
        message_template = re.compile(r"\d+")
        messages_hidden = [
            message_template.sub("N", str(m))
            for m in followed_hidden.context["messages"]
        ]
        messages_missing = [
            message_template.sub("N", str(m))
            for m in followed_missing.context["messages"]
        ]
        self.assertEqual(
            messages_hidden,
            messages_missing,
            "flash-message templates must be identical (only IDs differ)",
        )
        self.assertNotIn(
            self.the_superuser.email,
            followed_hidden.content.decode(),
            "the protected account's email must never appear",
        )
        self._assert_superuser_hidden()

    def test_changelist_hides_superuser_rows(self):
        """The changelist for a non-superuser must not expose superuser
        accounts (queryset-level hiding, accounts/admin.py:get_queryset).
        """
        self._grant(self.view_admin, "view_user")
        self.client.force_login(self.view_admin)
        response = self.client.get(reverse("admin:accounts_user_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.the_superuser.email)
        self.assertContains(response, self.client_user.email)
        self._assert_superuser_hidden()

    def test_change_view_hidden_superuser_matches_missing_object(self):
        """Direct change URL (GET and POST) for a superuser row responds
        exactly like a nonexistent User for a non-superuser, and any attack
        POST is a no-op on the protected account.
        """
        self._grant(self.view_admin, "change_user")
        self.client.force_login(self.view_admin)
        self._assert_equivocal_response("admin:accounts_user_change")
        attack = self._change_payload(
            self.the_superuser,
            is_superuser="off",  # attack: demote the superuser
            is_staff="off",
        )
        self._assert_equivocal_response(
            "admin:accounts_user_change", method="post", data=attack
        )
        self.the_superuser.refresh_from_db()
        self.assertTrue(self.the_superuser.is_superuser)
        self.assertTrue(self.the_superuser.is_staff)

    def test_delete_view_hidden_superuser_matches_missing_object(self):
        """Direct delete URL (GET and POST) for a superuser row responds
        exactly like a nonexistent User for a non-superuser, and the POST
        never deletes the protected account.
        """
        self._grant(self.view_admin, "delete_user")
        self.client.force_login(self.view_admin)
        self._assert_equivocal_response("admin:accounts_user_delete")
        self._assert_equivocal_response("admin:accounts_user_delete", method="post")
        self._assert_superuser_hidden()

    def test_history_view_hidden_superuser_matches_missing_object(self):
        """Direct admin history URL for a superuser row responds exactly
        like a nonexistent User for a non-superuser.
        """
        self._grant(self.view_admin, "view_user")
        self.client.force_login(self.view_admin)
        self._assert_equivocal_response("admin:accounts_user_history")
        self._assert_superuser_hidden()

    # ---------------- E. Self-protection ---------------------------------
    def test_non_superuser_cannot_delete_own_account(self):
        """A non-superuser administrator cannot delete their own account via
        the admin delete view; the account must survive both the denial and
        the verification.
        """
        self._grant(self.view_admin, "delete_user")
        self.client.force_login(self.view_admin)
        url = reverse("admin:accounts_user_delete", args=(self.view_admin.pk,))
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 403, "self-deletion must be denied (GET)"
        )
        response = self.client.post(url)
        self.assertEqual(
            response.status_code, 403, "self-deletion must be denied (POST)"
        )
        self.assertTrue(
            User.objects.filter(pk=self.view_admin.pk).exists(),
            "own account must survive a denied self-deletion",
        )

    # ---------------- F. Superuser positive controls ---------------------
    def test_superuser_retains_useradmin_control(self):
        """Positive control: a real superuser can still (a) see superuser
        rows in the changelist, (b) open the add view, (c) change flags on
        another user, and (d) save those changes to the database. Guards
        added for non-superusers must not weaken superuser capability.
        """
        self.client.force_login(self.the_superuser)
        response = self.client.get(reverse("admin:accounts_user_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.the_superuser.email)

        response = self.client.get(reverse("admin:accounts_user_add"))
        self.assertEqual(response.status_code, 200)

        target = self.client_user
        response = self.client.post(
            reverse("admin:accounts_user_change", args=(target.pk,)),
            self._change_payload(
                target,
                role=User.Role.PATIENT,  # role is a required, editable field for superusers
                is_staff="on",  # legitimate grant by the superuser
            ),
        )
        self.assertEqual(
            response.status_code,
            302,
            self._why_not_saved(response),
        )
        target.refresh_from_db()
        self.assertTrue(target.is_staff, "superuser legitimacy control: grant failed")
        # Restore the boundary for the positive control's lifecycle.
        target.is_staff = False
        target.save(update_fields=["is_staff"])
        target.refresh_from_db()
        self.assertFalse(target.is_staff)

    def test_superuser_can_add_user_with_privileges(self):
        """Positive control for add: only a superuser may provision staff
        accounts (is_staff=on) through the admin add form, and the chosen
        role sticks.
        """
        self.client.force_login(self.the_superuser)
        before = User.objects.count()
        response = self.client.post(
            reverse("admin:accounts_user_add"),
            {
                "email": "sup-added@example.com",
                "password1": PASSWORD,
                "password2": PASSWORD,
                "role": User.Role.RECEPTIONIST,
                "is_staff": "on",
            },
        )
        self.assertEqual(response.status_code, 302, self._why_not_saved(response))
        created = User.objects.filter(email="sup-added@example.com").first()
        self.assertIsNotNone(created, "superuser add must create the account")
        self.assertEqual(User.objects.count(), before + 1)
        self.assertEqual(created.role, User.Role.RECEPTIONIST)
        self.assertTrue(created.is_staff)
        self.assertFalse(created.is_superuser)
        self.assertTrue(created.check_password(PASSWORD))


class SeedDemoReceptionistsCommandTests(TestCase):
    CMD = "seed_demo_receptionists"
    EMAILS = (
        "ramprasad.reception@careclinic.example",
        "rishabh.reception@careclinic.example",
    )

    def test_creates_two_receptionists_with_unusable_passwords(self):
        call_command(self.CMD)
        self.assertEqual(User.objects.count(), 2)
        for email in self.EMAILS:
            user = User.objects.filter(email=email).first()
            self.assertIsNotNone(user, email)
            self.assertEqual(user.role, User.Role.RECEPTIONIST, email)
            self.assertFalse(user.is_staff, email)
            self.assertFalse(user.is_superuser, email)
            self.assertFalse(user.check_password("anything-at-all"), email)

    def test_rerun_is_idempotent_and_preserves_usable_passwords(self):
        call_command(self.CMD)
        ramprasad = User.objects.get(email=self.EMAILS[0])
        ramprasad.set_password("Admin-set-local-pw!")
        ramprasad.save(update_fields=["password"])
        call_command(self.CMD)
        self.assertEqual(User.objects.count(), 2)
        ramprasad.refresh_from_db()
        self.assertTrue(ramprasad.check_password("Admin-set-local-pw!"))
        rishabh = User.objects.get(email=self.EMAILS[1])
        self.assertFalse(rishabh.check_password("Admin-set-local-pw!"))

    def test_conflicting_reserved_email_fails_safely(self):
        User.objects.create_user(
            email=self.EMAILS[0],
            password="S3cret-pass!",
            role=User.Role.PATIENT,
        )
        before = User.objects.count()
        with self.assertRaises(Exception):
            call_command(self.CMD)
        # The whole command runs inside one transaction: nothing seeded.
        self.assertEqual(User.objects.count(), before)
        self.assertFalse(User.objects.filter(email=self.EMAILS[1]).exists())
