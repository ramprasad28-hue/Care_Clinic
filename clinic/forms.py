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
"""
from django import forms

from website.image_validation import (
    PORTRAIT_MIN_WIDTH,
    SECTION_MIN_WIDTH,
    validate_upload_image,
)

from .models import AvailabilityRule, Doctor, DoctorLeave, Speciality


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
    """Portrait: identity-critical — a narrow upload is warned about."""

    image_field = "profile_image"
    warn_width = PORTRAIT_MIN_WIDTH

    class Meta:
        model = Doctor
        fields = "__all__"
