"""Forms for the dashboards app.

Two concerns live here:

* :class:`AppointmentFilterForm` — validated, optional search/filter controls
  (date, status, doctor, patient, reference, scope). Invalid input yields form
  errors instead of a 500; the bound queryset is only filtered by valid data.
* :class:`ReceptionBookingForm` — book-on-behalf. Both ``patient`` and
  ``doctor`` are ``ModelChoiceField``s, so a submitted id is validated against
  the database before the transactional service is called (never trusted raw).
"""
from django import forms

from accounts.models import User
from appointments.forms import SlotChoiceFormMixin
from appointments.models import AppointmentStatus
from clinic.models import Doctor

PATIENTS = User.objects.filter(role=User.Role.PATIENT)

SCOPE_CHOICES = (
    ("upcoming", "Upcoming"),
    ("today", "Today"),
    ("past", "Past"),
    ("all", "All"),
)


class AppointmentFilterForm(forms.Form):
    """Optional filters, used by the receptionist and admin dashboards."""

    scope = forms.ChoiceField(required=False, choices=SCOPE_CHOICES)
    date = forms.DateField(
        required=False, widget=forms.DateInput(attrs={"type": "date"})
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "All statuses")] + list(AppointmentStatus.choices),
    )
    doctor = forms.ModelChoiceField(
        required=False,
        queryset=Doctor.objects.select_related("user").all(),
        empty_label="All doctors",
    )
    patient = forms.ModelChoiceField(
        required=False,
        queryset=PATIENTS.order_by("first_name", "email"),
        empty_label="All patients",
    )
    reference = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "e.g. CC-2026-000123"}),
    )

    def __init__(self, *args, fields=None, **kwargs):
        """Optionally restrict the visible fields per dashboard."""
        super().__init__(*args, **kwargs)
        if fields is not None:
            for name in list(self.fields):
                if name not in fields:
                    del self.fields[name]


class ReceptionBookingForm(SlotChoiceFormMixin, forms.Form):
    """Receptionist books a slot on behalf of a patient."""

    patient = forms.ModelChoiceField(
        queryset=PATIENTS.order_by("first_name", "email"),
        label="Patient",
    )
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.select_related("user").all(),
        label="Doctor",
        widget=forms.HiddenInput,
    )
    date = forms.DateField(required=False, widget=forms.HiddenInput)
    slot = forms.ChoiceField(
        choices=(), widget=forms.RadioSelect, label="Available slot"
    )
    reason = forms.CharField(
        required=False,
        max_length=255,
        label="Reason for visit (optional)",
        widget=forms.Textarea(attrs={"rows": 2}),
    )

    def __init__(self, *args, doctor=None, day=None, **kwargs):
        super().__init__(*args, doctor=doctor, day=day, **kwargs)
