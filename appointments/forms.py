"""Forms for the booking, cancellation, and rescheduling pages.

The forms only collect *intent* (which slot, optional reason). All authorization
and integrity rules are re-checked in :mod:`appointments.services` — the forms
never trust submitted ids.
"""
from django import forms
from django.utils import timezone

from .selectors import available_slots


class SlotChoiceFormMixin:
    """Populate a ``slot`` radio field from a doctor's available slots on a day."""

    def __init__(self, *args, doctor=None, day=None, now=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.doctor = doctor
        self.day = day
        now = now or timezone.now()
        choices = []
        if doctor is not None and day is not None:
            for slot in available_slots(doctor, day, now=now):
                choices.append(
                    (slot.pk, f"{slot.start_time:%H:%M} – {slot.end_time:%H:%M}")
                )
        self.fields["slot"].choices = choices
        self.fields["slot"].widget.choices = choices
        self.has_slots = bool(choices)


class BookingForm(SlotChoiceFormMixin, forms.Form):
    slot = forms.ChoiceField(
        choices=(), widget=forms.RadioSelect, label="Available slot"
    )
    reason = forms.CharField(
        required=False,
        max_length=255,
        label="Reason for visit (optional)",
        widget=forms.Textarea(attrs={"rows": 2}),
    )


class RescheduleForm(SlotChoiceFormMixin, forms.Form):
    slot = forms.ChoiceField(
        choices=(), widget=forms.RadioSelect, label="New slot"
    )


class CancelForm(forms.Form):
    reason = forms.CharField(
        required=False,
        max_length=255,
        label="Reason (optional)",
        widget=forms.Textarea(attrs={"rows": 2}),
    )
