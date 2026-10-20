"""Admin forms for the website section-image registry (ADR-022, phase C1)."""
from django import forms

from website.image_validation import SECTION_MIN_WIDTH, validate_upload_image

from .models import WebsiteSectionImage


class WebsiteSectionImageAdminForm(forms.ModelForm):
    """Upload validation for a registered section image (warnings-only dims)."""

    warn_width = SECTION_MIN_WIDTH

    def clean(self):
        cleaned = super().clean()
        self.image_warnings = validate_upload_image(
            cleaned.get("image"),
            warn_width=self.warn_width,
        )
        return cleaned

    class Meta:
        model = WebsiteSectionImage
        fields = "__all__"
