"""Website imagery registry (ADR-022, phase C1).

``WebsiteSectionImage`` lets administrators upload/replace the photographs of
the documented, existing website sections **through Django Admin only** —
templates keep the pre-C1 static fallback chain whenever an upload is absent
(or the registry row is inactive), so removing an image degrades exactly as a
missing static file does today. No new image-led sections are invented: the
stable keys map to sections that already exist (see
``docs/phase-c1-admin-managed-imagery-plan.md`` §2C).

Uploads live under ``MEDIA_ROOT`` (``sections/``), separate from the
source-controlled ``static/img`` — an admin upload can never overwrite a
repo asset.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

#: Stable, never content-derived section identifiers. Keys map 1:1 to real
#: template slots inventoried in the C1 plan; new keys can be appended later
#: and the template tag fails closed (fallback) for unknown ones.
SECTION_KEYS = (
    ("home_hero", _("Homepage hero")),
    ("home_about", _("Homepage about band")),
    ("auth_login_panel", _("Login visual panel")),
    ("auth_register_panel", _("Register visual panel")),
    ("doctors_listing_header", _("Doctor listing header")),
    ("doctor_profile_photo_aside", _("Doctor profile aside photo")),
    ("specialities_mega_feature", _("Specialities mega-menu feature")),
    ("doctors_mega_feature", _("Doctors mega-menu feature")),
)

#: Static fallback for each key: the exact file/alt/caption rendering the
#: approved F6 frontend shows today, so an absent upload is a visual no-op.
SECTION_STATIC_FALLBACKS = {
    "home_hero": {
        "static_path": "img/home/hero-main.jpg",
        "alt": "",
        "caption": "",
    },
    "home_about": {
        "static_path": "img/about/waiting-area.jpg",
        "alt": "A calm, tidy clinic consultation room with a wooden desk and two chairs",
        "caption": (
            "Illustrative stock photo — a calm clinic consultation room. "
            "Care_Clinic itself shows only real data: actual specialities, "
            "doctors who are accepting appointments, and their genuine open times."
        ),
    },
    "auth_login_panel": {
        "static_path": "img/home/hero-main.jpg",
        "alt": (
            "A clinician in a white coat warmly welcoming a smiling patient in a "
            "light-filled consultation room — illustrative stock photograph"
        ),
        "caption": "Illustrative stock photograph — not a Care_Clinic premises",
    },
    "auth_register_panel": {
        "static_path": "img/about/waiting-area.jpg",
        "alt": "A calm, tidy clinic consultation room with a wooden desk and two chairs — illustrative stock photograph",
        "caption": "Illustrative stock photograph — not a Care_Clinic premises",
    },
    "doctors_listing_header": {
        "static_path": "img/about/waiting-area.jpg",
        "alt": "",
        "caption": "Illustrative stock photo — not the clinic's premises.",
    },
    "doctor_profile_photo_aside": {
        "static_path": "img/home/hero-main.jpg",
        "alt": "",
        "caption": (
            "Illustrative stock photo — not a photograph of Dr. {doctor_name}."
        ),
    },
    "specialities_mega_feature": {
        "static_path": "img/about/waiting-area.jpg",
        "alt": "",
        "caption": "",
    },
    "doctors_mega_feature": {
        "static_path": "img/home/hero-main.jpg",
        "alt": "",
        "caption": "",
    },
}


def section_image_path(instance, filename):
    """Upload scope for website sections (never touches source-controlled static/)."""
    ext = (filename.rsplit(".", 1)[-1] or "jpg").lower()
    return f"sections/{instance.key or 'unassigned'}/image.{ext}"


class WebsiteSectionImageQuerySet(models.QuerySet):
    def active_for(self, key):
        """The active registry row for ``key`` that has an upload, or ``None``."""
        return self.filter(key=key, is_active=True).exclude(image="").first()


class WebsiteSectionImage(models.Model):
    """One admin-managed photograph per stable website section key."""

    key = models.SlugField(
        _("section key"),
        max_length=60,
        unique=True,
        choices=SECTION_KEYS,
        help_text=_(
            "Stable identifier of the website section this image feeds. "
            "Unknown keys stay on their template fallback."
        ),
    )
    name = models.CharField(
        _("name"),
        max_length=120,
        unique=True,
        help_text=_("Human-readable label shown in the admin (e.g. 'Homepage hero')."),
    )
    image = models.ImageField(_("image"), upload_to=section_image_path, null=True, blank=True)
    alt_text = models.CharField(
        _("alt text"),
        max_length=255,
        blank=True,
        help_text=_(
            "Text alternative for the uploaded image. Leave empty only when the "
            "image is purely decorative."
        ),
    )
    caption = models.CharField(
        _("caption"),
        max_length=255,
        blank=True,
        help_text=_("Optional honest caption replacing the template's default wording."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Deactivate to revert this section to its static fallback."),
    )
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    objects = WebsiteSectionImageQuerySet.as_manager()

    class Meta:
        verbose_name = _("website section image")
        verbose_name_plural = _("website section images")
        ordering = ["key"]

    def __str__(self):
        return self.name

    @property
    def fallback(self):
        """Static-fallback metadata for this row's key (always a dict)."""
        return SECTION_STATIC_FALLBACKS.get(self.key, {})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
