"""Forms for doctor self-service availability and leave management.

The ``doctor``/ownership field is deliberately NOT part of these forms — it is
forced by the view from ``request.user`` so a doctor can never attribute a
record to another doctor by tampering with submitted data.

Administrator-managed imagery (ADR-022, phase C1) also lives here: the admin
``ModelForm`` subclasses below extend Django's default behaviour (nothing is
replaced) with upload validation — hard errors for unsupported
type/extension, non-decodable content, and oversized files; dimension/ratio
guidance is collected as ``form.image_warnings`` and surfaced as admin
warning messages by the ModelAdmin after a successful save.

DoctorAdminForm additionally supports two account modes on *add* (Django
admin Doctors > Add doctor):

* ``existing`` — the original workflow: pick an eligible DOCTOR-role user
  that does not yet have a Doctor profile.
* ``new`` — provision a fresh DOCTOR-role account from the same page. The
  role is forced server-side to DOCTOR (the submitted data contains no role
  field at all, so ADMIN/other privileged roles cannot be selected), the
  password is hashed through the standard User manager API, the user is
  created atomically together with the Doctor profile (admin saves
  inside one transaction block, so a failing profile save rolls the user
  back), and validation degrades gracefully: with JavaScript unavailable the
  account fields are simply always rendered and the server is the
  authoritative gatekeeper.
"""
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from website.image_validation import (
    PORTRAIT_MIN_WIDTH,
    SECTION_MIN_WIDTH,
    validate_upload_image,
)

from .models import (
    AvailabilityRule,
    Doctor,
    DoctorLeave,
    OneDayAvailability,
    Speciality,
)
User = get_user_model()

ACCOUNT_MODE_EXISTING = "existing"
ACCOUNT_MODE_NEW = "new"


class AvailabilityRuleForm(forms.ModelForm):
    class Meta:
        model = AvailabilityRule
        fields = ("weekday", "start_time", "end_time", "slot_length_minutes", "is_active")
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
            "end_time": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_time"].input_formats = ["%H:%M", "%H:%M:%S"]
        self.fields["end_time"].input_formats = ["%H:%M", "%H:%M:%S"]

class OneDayAvailabilityForm(forms.ModelForm):
    """Form for availability that applies to one specific date."""

    class Meta:
        model = OneDayAvailability
        fields = (
            "date",
            "start_time",
            "end_time",
            "slot_length_minutes",
            "is_active",
        )
        widgets = {
            "date": forms.DateInput(
                attrs={"type": "date"},
                format="%Y-%m-%d",
            ),
            "start_time": forms.TimeInput(
                attrs={"type": "time"},
                format="%H:%M",
            ),
            "end_time": forms.TimeInput(
                attrs={"type": "time"},
                format="%H:%M",
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].input_formats = ["%Y-%m-%d"]
        self.fields["start_time"].input_formats = ["%H:%M", "%H:%M:%S"]
        self.fields["end_time"].input_formats = ["%H:%M", "%H:%M:%S"]

class DoctorLeaveForm(forms.ModelForm):
    class Meta:
        model = DoctorLeave
        fields = ("start_date", "end_date", "reason")
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class ImageAdminFormMixin:
    """Shared clean() plumbing for forms with one uploadable image field."""

    image_field = "image"
    warn_width = None
    warn_ratio = None

    def clean(self):
        cleaned = super().clean()
        self.image_warnings = validate_upload_image(
            cleaned.get(self.image_field),
            warn_width=self.warn_width,
            warn_ratio=self.warn_ratio,
        )
        return cleaned


class SpecialityAdminForm(ImageAdminFormMixin, forms.ModelForm):
    """Card/hero tile: editorial 3:2 box, mismatches warn only."""

    image_field = "image"
    warn_width = SECTION_MIN_WIDTH
    warn_ratio = "3/2"

    class Meta:
        model = Speciality
        fields = "__all__"


class DoctorAdminForm(ImageAdminFormMixin, forms.ModelForm):
    """Portrait: identity-critical — a narrow upload is warned about.

    Extends the base behaviour with the dual account-mode workflow (see the
    module docstring). The extra account fields are declared only when the
    form is *adding* (creating) a Doctor; change circles remain exactly as
    before.
    """

    image_field = "profile_image"
    warn_width = PORTRAIT_MIN_WIDTH

    new_account_field_names = (
        "new_first_name",
        "new_last_name",
        "new_email",
        "new_phone",
        "new_password1",
        "new_password2",
    )
    add_only_field_names = ("account_mode", *new_account_field_names)

    # Declared at class level (required=False) because ``ModelAdmin.get_form``
    account_mode = forms.ChoiceField(
        label=_("User account"),
        choices=(
            (ACCOUNT_MODE_EXISTING, _("Select existing user")),
            (ACCOUNT_MODE_NEW, _("Create new doctor account")),
        ),
        initial=ACCOUNT_MODE_EXISTING,
        widget=forms.Select(attrs={"data-account-mode-selector": "true"}),
    )
    new_first_name = forms.CharField(
        label=_("First name"), max_length=150, required=False
    )
    new_last_name = forms.CharField(
        label=_("Last name"), max_length=150, required=False
    )
    new_email = forms.EmailField(label=_("Email"), max_length=254, required=False)
    new_phone = forms.CharField(
        label=_("Phone number"),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"type": "tel"}),
    )
    new_password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        required=False,
        widget=forms.PasswordInput,
    )
    new_password2 = forms.CharField(
        label=_("Confirm password"),
        strip=False,
        required=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = Doctor
        fields = "__all__"

    class Media:
        js = ("js/admin/doctor_account_mode.js",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._creating_user = False
        if self.instance.pk is None:
            # Add mode: activate the account fields. All of them are
            # required=False *at the form level* so they never fire for the
            # other mode; the mode-dependent validation in clean() is the
            # single gatekeeper.
            self.fields["user"].required = False
            # Only DOCTOR-role users without an existing profile may own a new
            # Doctor. Scope the queryset to *add* requests only: on change,
            # the doctor's own user already has a profile and must remain a
            # valid choice.
            self.fields["user"].queryset = User.objects.filter(
                role=User.Role.DOCTOR
            ).exclude(doctor__isnull=False)
        else:
            # Change mode: drop the account-mode machinery entirely.
            for name in self.add_only_field_names:
                self.fields.pop(name, None)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def clean(self):
        cleaned = super().clean()
        # Image warnings are attached by ImageAdminFormMixin's own clean(); here
        # we only layer the account-mode validation. getattr-safe because the
        # parent clean() may return a plain dict on additive binding orders.
        self.image_warnings = getattr(self, "image_warnings", [])

        if self.instance.pk is not None:
            return cleaned  # change mode: nothing account related to layer

        mode = (cleaned.get("account_mode") or ACCOUNT_MODE_EXISTING).strip()
        if mode not in (ACCOUNT_MODE_EXISTING, ACCOUNT_MODE_NEW):
            # Tampered select value: reject rather than guessing an intent.
            self.add_error("account_mode", _("Unknown user account mode."))
            return cleaned

        if mode == ACCOUNT_MODE_EXISTING:
            user = cleaned.get("user")
            if user is None:
                self.add_error(
                    "user",
                    _("Please select an existing DOCTOR-role user, or switch the “User account” selector to “Create new doctor account”."),
                )
            else:
                # Server-side re-checks (authoritative even for manual posts):
                if user.role != User.Role.DOCTOR:
                    self.add_error(
                        "user",
                        _("The selected user does not have the DOCTOR role."),
                    )
                if Doctor.objects.filter(user=user).exists():
                    self.add_error(
                        "user",
                        _("This user already has a Doctor profile."),
                    )
            for name in self.new_account_field_names:
                cleaned.pop(name, None)
            self._creating_user = False
        else:  # ACCOUNT_MODE_NEW
            # The existing-user selector is irrelevant (and hidden client-side);
            # a manually submitted user id must not win here.
            cleaned["user"] = None

            required = {
                "new_first_name": _("First name"),
                "new_email": _("Email"),
                "new_password1": _("Password"),
                "new_password2": _("Confirm password"),
            }
            for name, label in required.items():
                if not (cleaned.get(name) or "").strip():
                    self.add_error(name, _("This field is required."))
            first_name = (cleaned.get("new_first_name") or "").strip()
            last_name = (cleaned.get("new_last_name") or "").strip()
            email = (cleaned.get("new_email") or "").strip()
            phone = (cleaned.get("new_phone") or "").strip()
            password1 = cleaned.get("new_password1") or ""
            password2 = cleaned.get("new_password2") or ""

            if email:
                if User.objects.filter(email__iexact=email).exists():
                    self.add_error(
                        "new_email",
                        _("An account with this email address already exists."),
                    )
            if password1 and password2 and password1 != password2:
                self.add_error(
                    "new_password2", _("The two password fields did not match.")
                )
            if not self.has_error("new_password1") and password1:
                try:
                    password_validation.validate_password(password1)
                except forms.ValidationError as exc:
                    self.add_error("new_password1", exc.messages)

            if not self.has_error("new_email") and email:
                # Keep a tentatively created user for password validation by
                # the framework (validate_password uses user attributes like
                # the email for similarity checks).
                self._pending_user_attrs = {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone,
                }

            self._creating_user = True
        return cleaned

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------
    def save(self, commit=True):
        """Create-swap: provision the account, then link and save the Doctor.

        The transaction is entered around *both* operations: if the Doctor
        save fails, the freshly created User is rolled back so no orphan
        account is left behind. In the Django admin flow the surrounding
        change-view transaction also protects ``save(commit=False)`` usage,
        so users are never left stranded when the ModelAdmin raises later in
        the request.
        """
        if not self._creating_user:
            return super().save(commit)

        attrs = getattr(self, "_pending_user_attrs", {})
        with transaction.atomic():
            user = User.objects.create_user(
                email=attrs["email"],
                password=self.cleaned_data["new_password1"],
                first_name=attrs.get("first_name", ""),
                last_name=attrs.get("last_name", ""),
                phone=attrs.get("phone", ""),
                role=User.Role.DOCTOR,
            )
            self.instance.user = user
            return super().save(commit)
