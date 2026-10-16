"""Custom user model.

Email is the unique login identifier (USERNAME_FIELD). Role is an explicit
field with four choices. Django Groups/Permissions remain available through
PermissionsMixin. Public registration (Phase 3) must create PATIENT accounts
only; privileged roles are provisioned by an administrator.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        PATIENT = "PATIENT", _("Patient")
        DOCTOR = "DOCTOR", _("Doctor")
        RECEPTIONIST = "RECEPTIONIST", _("Receptionist")
        ADMIN = "ADMIN", _("Administrator")

    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT,
        help_text=_("Authorization role. Defaults to Patient."),
    )
    phone = models.CharField(_("phone number"), max_length=20, blank=True)

    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Inactive users cannot authenticate."),
    )
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Grants access to the Django admin site."),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email + password are the only required fields

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["email"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def get_short_name(self):
        return self.first_name or self.email

    # --- Role convenience predicates -------------------------------------
    def has_role(self, *roles):
        """Return True if the user holds any of the given roles.

        Superusers are treated as holding every role so an administrator is
        never locked out of a role-gated view. ``roles`` accepts role string
        values (``User.Role`` members compare equal to their values).
        """
        if self.is_superuser:
            return True
        return self.role in roles

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_doctor(self):
        return self.role == self.Role.DOCTOR

    @property
    def is_receptionist(self):
        return self.role == self.Role.RECEPTIONIST

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN
