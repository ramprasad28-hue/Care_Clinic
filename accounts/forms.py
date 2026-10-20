"""Forms for authentication and registration.

Security note: the public registration form NEVER reads a role from input.
The created account's role is hard-coded to PATIENT (see ADR-012). Any
``role`` field submitted by a client is ignored.
"""
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UsernameField
from django.core.exceptions import ValidationError

from .models import User


class EmailAuthenticationForm(AuthenticationForm):
    """Login form that labels the identifier field as Email."""

    username = UsernameField(
        label="Email",
        widget=forms.EmailInput(
            attrs={"autofocus": True, "autocomplete": "email", "spellcheck": "false"}
        ),
    )


class PatientRegistrationForm(UserCreationForm):
    """Self-service registration restricted to the Patient role."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "email", "phone")
        widgets = {
            "first_name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "last_name": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(
                attrs={"autocomplete": "email", "spellcheck": "false"}
            ),
            "phone": forms.TextInput(
                attrs={"type": "tel", "inputmode": "tel", "autocomplete": "tel"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ("password1", "password2"):
            self.fields[field_name].widget.attrs.update(
                {"autocomplete": "new-password"}
            )

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data["email"])
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Role is forced server-side; never trust a submitted "role".
        user.role = User.Role.PATIENT
        if commit:
            user.save()
        return user
