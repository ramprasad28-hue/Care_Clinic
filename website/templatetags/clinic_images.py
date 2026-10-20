"""Template helpers for optional, self-hosted imagery.

Resolution order per surface (ADR-022, phase C1):

1. administrator upload (Django Admin) — a real media URL;
2. the documented static fallback file (only when it exists);
3. empty string — the caller renders no broken ``<img>`` (initials/text
   fallbacks kick in instead).

Static fallbacks are filesystem-probed against ``STATICFILES_DIRS`` (dev) /
``STATIC_ROOT`` (collected/prod): a missing file degrades gracefully and a
removed image never leaves a broken ``<img>`` behind. Honesty rules
(docs/imagery-licensing.md) live in the calling templates/captions/alt text,
not here. Callers receive ready-to-use URLs — no second ``{% static %}`` hop.
"""
import os

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


def _file_in_static(relative_path):
    for path in settings.STATICFILES_DIRS:
        if os.path.isfile(os.path.join(str(path), str(relative_path))):
            return True
    static_root = getattr(settings, "STATIC_ROOT", None)
    if static_root and os.path.isfile(os.path.join(str(static_root), str(relative_path))):
        return True
    return False


@register.filter
def static_exists(relative_path):
    """True when ``relative_path`` exists in a configured static directory."""
    return _file_in_static(relative_path)


@register.simple_tag
def doctor_portrait(doctor):
    """Ready-to-use portrait URL for a doctor, or ``""`` when none.

    Admin upload first (presumed a genuine, consented photograph per the
    imagery-manifest honesty rules), then the slug-mapped static demo
    placeholder ``static/img/doctors/<slug>-profile.webp`` if the file
    exists, else ``""`` (callers keep the initials avatar — a missing file
    never renders a broken ``<img>``).
    """
    upload = getattr(doctor, "profile_image", None)
    if upload:
        try:
            return upload.url
        except ValueError:  # no file bound (e.g. field saved as None)
            pass
    slug = getattr(doctor, "slug", "") or ""
    if not slug:
        return ""
    relative = f"img/doctors/{slug}-profile.webp"
    return static(relative) if _file_in_static(relative) else ""


@register.simple_tag
def speciality_tile_image(speciality):
    """Ready-to-use tile/hero image URL for a speciality, or ``""``.

    Admin upload first, then the documented static placeholder
    ``static/img/specialities/<slug>-card.jpg`` when it exists. Everything
    that renders this image (homepage/listing cards, the specialities mega
    menu, the speciality detail page-hero) resolves the same image here.
    """
    upload = getattr(speciality, "image", None)
    if upload:
        try:
            return upload.url
        except ValueError:
            pass
    slug = getattr(speciality, "slug", "") or ""
    if not slug:
        return ""
    relative = f"img/specialities/{slug}-card.jpg"
    return static(relative) if _file_in_static(relative) else ""


@register.simple_tag
def section_image(key, doctor=None):
    """Resolve a registered website section's image metadata (ADR-022).

    Returns ``None`` or a dict::

        {"url": <ready-to-use URL>, "alt": <str>, "caption": <str>, "uploaded": bool}

    Resolution: the active registry row's upload (``website.WebsiteSectionImage``,
    ``is_active=True`` with an image), else the static fallback file **only
    when it exists**. Unknown keys fail closed (``None``), so future template
    edits can adopt the tag without inventing imagery.
    """
    from ..models import SECTION_STATIC_FALLBACKS, WebsiteSectionImage

    fallback = SECTION_STATIC_FALLBACKS.get(key)
    if fallback is None:
        return None

    row = WebsiteSectionImage.objects.active_for(key) if key else None
    default_alt = fallback.get("alt", "")
    default_caption = fallback.get("caption", "")
    caption = default_caption
    alt = default_alt
    if doctor is not None and caption:
        caption = caption.format(doctor_name=doctor.user.get_full_name())
    if row is not None:
        try:
            url = row.image.url
        except ValueError:
            url = None
        if url is not None:
            alt = row.alt_text or default_alt
            caption = row.caption or caption
            return {"url": url, "alt": alt, "caption": caption, "uploaded": True}

    static_path = fallback.get("static_path", "")
    if static_path and _file_in_static(static_path):
        return {"url": static(static_path), "alt": alt, "caption": caption, "uploaded": False}
    return None
