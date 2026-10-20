"""Shared validation for administrator-uploaded images (ADR-022).

Rules implemented from the C1 plan docs/phase-c1-admin-managed-imagery-plan.md §3:

* type allowlist enforced by **content**, not extension alone: the file must be
  decodable by Pillow and its real format must be JPEG, PNG, or WebP (SVG is
  rejected outright — scriptable content).
* a setting-driven size cap (default ~2 MB, override with
  ``UPLOAD_IMAGE_MAX_BYTES``).
* dimension guidance: dimension mismatches are **warnings** (surfaced as
  admin warning messages after a successful save), never silent rejection —
  an otherwise valid image whose ratio differs from the editorial box is
  still accepted (rule: prefer warnings over rejecting valid images).

The module is a plain mixin of functions (no Django model imports) so both
``clinic`` and ``website`` can use it without import cycles.
"""
import io

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

#: Hard dimension floors (identity-critical portraits only; see plan §6.4):
#: a portrait narrower than this is accepted, but flagged as a warning.
PORTRAIT_MIN_WIDTH = 480
#: Editorial minimums for section/hero artwork (warning-only as well).
SECTION_MIN_WIDTH = 900

_ALLOWED_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")
_ALLOWED_PIL_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})


def max_upload_bytes():
    """Configured upload cap. Default 2 MiB, overridable via settings."""
    return getattr(settings, "UPLOAD_IMAGE_MAX_BYTES", 2 * 1024 * 1024)


def image_name_lower(image_field_file):
    """Lowercase display name of an uploaded file ("" when unset)."""
    if not image_field_file:
        return ""
    return (image_field_file.name or "").rsplit("/", 1)[-1].lower()


def has_file(image_field_file):
    """True when an actual file is bound (upload present, not cleared/blank)."""
    return bool(image_field_file and getattr(image_field_file, "file", None) is not None)


def validate_upload_image(
    image_field_file,
    *,
    warn_width=None,
    warn_ratio=None,
):
    """Validate one uploaded image.

    Hard rules raise ``ValidationError`` (extension allowlist, decodeable
    content, decoded format allowlist, size cap). Soft guidance is returned
    as a list of human-readable warning strings (dimension floor, ratio).

    ``warn_width`` — emit a warning when the decoded width is below this.
    ``warn_ratio`` — emit a warning when width/height differs from this
    ("w/h", e.g. "3/2"); purely editorial, never blocks the upload.
    """
    warnings = []
    if not has_file(image_field_file):
        return warnings

    name = image_name_lower(image_field_file)
    if not name or not name.endswith(_ALLOWED_EXTENSIONS):
        raise ValidationError(
            _(  # keep first line short for the admin form row
                "Unsupported image type. Allowed: JPG, JPEG, PNG, WebP "
                "(the file must really be one of these, not just named so)."
            )
        )

    try:
        image_field_file.seek(0)
    except (OSError, AttributeError):
        pass  # read from wherever the pointer currently is

    from PIL import Image, UnidentifiedImageError  # imported lazily: Pillow is an upload-time dependency only

    try:
        decoded = Image.open(io.BytesIO(image_field_file.read()))
        decoded.verify()
    except UnidentifiedImageError:
        raise ValidationError(
            _("This file is not a decodable image (JPG, PNG, WebP required).")
        )
    except Exception:
        raise ValidationError(
            _("This image could not be read as a valid JPG, PNG, or WebP file.")
        )
    finally:
        try:
            image_field_file.seek(0)
        except (OSError, AttributeError):
            pass

    try:
        size = image_field_file.size
    except (AttributeError, OSError):  # pragma: no cover - defensive
        size = None
    if size and size > max_upload_bytes():
        raise ValidationError(
            _("Image is too large (max %(max)s MB).") % {"max": round(max_upload_bytes() / (1024 * 1024))}
        )

    # Re-open after verify() for real dimensions.
    try:
        image_field_file.seek(0)
        with Image.open(io.BytesIO(image_field_file.read())) as reopened:
            width, height = reopened.size
            real_format = reopened.format
        image_field_file.seek(0)
    except Exception:
        raise ValidationError(
            _("This image could not be read as a valid JPG, PNG, or WebP file.")
        )
    if real_format not in _ALLOWED_PIL_FORMATS:
        raise ValidationError(
            _("Unsupported image content: decoded as %(kind)s. Allowed: JPG, PNG, WebP.")
            % {"kind": real_format or _("unknown")}
        )

    if warn_width and width and width < warn_width:
        warnings.append(
            f"{name}: image is {width}px wide — at least {warn_width}px is recommended for this slot."
        )
    if warn_ratio:
        try:
            want_w, want_h = (float(part) for part in warn_ratio.split("/", 1))
            if width and height and want_w and abs(width / height - want_w / want_h) > 0.35:
                warnings.append(
                    f"{name}: image ratio {width}:{height} differs from the slot's "
                    f"{want_w:g}:{want_h:g} box; it will be centre-cropped at display time."
                )
        except (ValueError, ZeroDivisionError):  # pragma: no cover - defensive
            pass
    return warnings
