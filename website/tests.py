"""Tests for the public website (home, specialities, doctors)."""
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import resolve, reverse

from clinic.models import AvailabilityRule, Doctor, Speciality, Weekday

User = get_user_model()


def make_speciality(name="Cardiology", is_active=True):
    return Speciality.objects.create(name=name, is_active=is_active)


def make_doctor(
    speciality,
    email,
    first_name="Doc",
    last_name="Smith",
    is_accepting=True,
    user_active=True,
    **kwargs,
):
    user = User.objects.create_user(
        email=email,
        password="S3cret-pass!",
        role=User.Role.DOCTOR,
        is_active=user_active,
        first_name=first_name,
        last_name=last_name,
    )
    return Doctor.objects.create(
        user=user,
        speciality=speciality,
        registration_number=f"REG-{email}",
        qualification=kwargs.pop("qualification", "MBBS"),
        is_accepting_appointments=is_accepting,
        **kwargs,
    )


class HomePageTests(TestCase):
    def test_home_ok_for_anonymous(self):
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_home_lists_active_speciality(self):
        make_speciality("Cardiology")
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Cardiology")


class SpecialityPageTests(TestCase):
    def test_list_shows_only_active(self):
        make_speciality("Cardiology", is_active=True)
        make_speciality("Dermatology", is_active=False)
        response = self.client.get(reverse("speciality_list"))
        self.assertContains(response, "Cardiology")
        self.assertNotContains(response, "Dermatology")

    def test_detail_active_ok(self):
        spec = make_speciality("Cardiology")
        response = self.client.get(spec.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cardiology")

    def test_detail_inactive_is_404(self):
        spec = make_speciality("Dermatology", is_active=False)
        self.assertEqual(self.client.get(spec.get_absolute_url()).status_code, 404)

    def test_detail_unknown_is_404(self):
        self.assertEqual(
            self.client.get(reverse("speciality_detail", kwargs={"slug": "nope"})).status_code,
            404,
        )


class DoctorPageTests(TestCase):
    def setUp(self):
        self.cardio = make_speciality("Cardiology")
        self.derma = make_speciality("Dermatology")
        self.accepting = make_doctor(
            self.cardio, "a@example.com", first_name="Alice", last_name="Anderson"
        )
        self.not_accepting = make_doctor(
            self.derma, "b@example.com", first_name="Bob", last_name="Brown",
            is_accepting=False,
        )

    def test_list_shows_only_accepting(self):
        response = self.client.get(reverse("doctor_list"))
        self.assertContains(response, "Alice Anderson")
        self.assertNotContains(response, "Bob Brown")

    def test_list_shows_doctor_name(self):
        response = self.client.get(reverse("doctor_list"))
        self.assertContains(response, self.accepting.user.get_full_name())

    def test_filter_by_speciality(self):
        other_cardio = make_doctor(
            self.cardio, "c@example.com", first_name="Carol", last_name="Clark"
        )
        response = self.client.get(reverse("doctor_list"), {"speciality": self.cardio.slug})
        self.assertContains(response, other_cardio.user.get_full_name())
        self.assertNotContains(response, "Bob Brown")

    def test_detail_accepting_ok(self):
        response = self.client.get(self.accepting.get_absolute_url())
        self.assertEqual(response.status_code, 200)

    def test_detail_non_accepting_is_404(self):
        self.assertEqual(
            self.client.get(self.not_accepting.get_absolute_url()).status_code, 404
        )

    def test_detail_unknown_is_404(self):
        self.assertEqual(
            self.client.get(reverse("doctor_detail", kwargs={"slug": "nope"})).status_code,
            404,
        )

    def test_inactive_user_hidden(self):
        hidden = make_doctor(
            self.cardio, "d@example.com", first_name="Dan", last_name="Davis",
            user_active=False,
        )
        self.assertEqual(self.client.get(hidden.get_absolute_url()).status_code, 404)


class DoctorDetailAvailabilityTests(TestCase):
    def test_detail_renders_availability(self):
        spec = make_speciality("Cardiology")
        doctor = make_doctor(spec, "a@example.com", first_name="Alice", last_name="Anderson")
        AvailabilityRule.objects.create(
            doctor=doctor,
            weekday=Weekday.MONDAY,
            start_time="09:00",
            end_time="11:00",
            slot_length_minutes=15,
        )
        response = self.client.get(doctor.get_absolute_url())
        self.assertContains(response, "Monday")
        self.assertContains(response, "15 min")


def make_user(email="user@example.com", role=User.Role.PATIENT, **kwargs):
    return User.objects.create_user(
        email=email, password="S3cret-pass!", role=role, **kwargs
    )


class SharedNavigationTests(TestCase):
    """The shared site header/nav in ``templates/base.html`` (Phase 7.5, 11).

    These lock the structural contract the CSS/JS rely on: landmarks, skip
    link, the mobile-toggle wiring, role-aware links, and the POST logout.
    """

    def test_skip_link_and_main_landmark(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'class="skip-link" href="#main-content"')
        self.assertContains(response, "Skip to main content")
        self.assertContains(response, 'id="main-content"')

    def test_progressive_enhancement_hook(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'class="no-js"')
        self.assertContains(response, "classList.remove('no-js')")

    def test_mobile_toggle_wiring(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'type="button" class="nav-toggle"')
        self.assertContains(response, 'aria-expanded="false"')
        self.assertContains(response, 'aria-controls="site-nav"')
        self.assertContains(response, 'id="site-nav"')
        self.assertContains(response, 'aria-label="Primary"')

    def test_primary_links_present_for_anonymous(self):
        response = self.client.get(reverse("home"))
        for name in ("speciality_list", "doctor_list", "accounts:login", "accounts:register"):
            self.assertContains(response, reverse(name))
        self.assertNotContains(response, reverse("dashboards:landing"))
        self.assertNotContains(response, reverse("appointments:list"))

    def test_active_link_uses_aria_current(self):
        response = self.client.get(reverse("doctor_list"))
        self.assertContains(response, 'aria-current="page"')

    def test_patient_sees_account_links_but_not_clinic_or_admin(self):
        self.client.force_login(make_user("p@example.com", User.Role.PATIENT))
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("dashboards:landing"))
        self.assertContains(response, reverse("appointments:list"))
        self.assertNotContains(response, "Django admin")
        self.assertNotContains(response, reverse("clinic:availability_list"))
        self.assertNotContains(response, reverse("clinic:leave_list"))

    def test_doctor_sees_clinic_links(self):
        self.client.force_login(make_user("d@example.com", User.Role.DOCTOR))
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("clinic:availability_list"))
        self.assertContains(response, reverse("clinic:leave_list"))
        self.assertNotContains(response, "Django admin")

    def test_staff_sees_admin_link(self):
        self.client.force_login(
            make_user("a@example.com", User.Role.ADMIN, is_staff=True)
        )
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("admin:index"))

    def test_logout_is_a_post_form(self):
        self.client.force_login(make_user("p@example.com", User.Role.PATIENT))
        response = self.client.get(reverse("home"))
        self.assertContains(
            response, f'<form method="post" action="{reverse("accounts:logout")}"'
        )
        self.assertContains(response, "csrfmiddlewaretoken")



# ==========================================================================
# Phase C1 — admin-managed imagery (ADR-022)
# ==========================================================================
import io
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from django.test import override_settings
from django.urls import reverse
from django.views.static import serve

from website.image_validation import (
    PORTRAIT_MIN_WIDTH,
    SECTION_MIN_WIDTH,
    max_image_dimension,
    max_upload_bytes,
    validate_upload_image,
)
from website.models import (
    SECTION_KEYS,
    SECTION_STATIC_FALLBACKS,
    WebsiteSectionImage,
)

#: A media root inside a temp dir — uploads never land on the repo or on
#: other tests' media files (nothing outside this test run reads it).
_TEMP_MEDIA_ROOT = tempfile.mkdtemp(prefix="c1-tests-media-")


def png_bytes(width=1200, height=800, color=(20, 130, 140)):
    """A real, decodable in-memory PNG (content, not just a filename)."""
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color).save(buffer, format="PNG")
    return buffer.getvalue()


def upload(name="image.png", data=None, content_type="image/png"):
    return SimpleUploadedFile(name, png_bytes() if data is None else data, content_type)


def png_header_only_bytes(width, height):
    """A minimal PNG containing only a signature and IHDR/IEND chunks.

    Pillow reads the declared dimensions from the header without allocating
    or decoding any pixels — safe for exercising the dimension guard.
    """
    import struct
    import zlib

    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(ctype, data):
        return (
            struct.pack(">I", len(data)) + ctype + data
            + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return (
        signature
        + chunk(b"IHDR", ihdr)
        + chunk(b"IEND", b"")
    )


class UploadImageValidationTests(TestCase):
    """Content-based validation shared by all three upload surfaces (ADR-022)."""

    def test_max_bytes_setting_default(self):
        self.assertEqual(max_upload_bytes(), 2 * 1024 * 1024)

    def test_valid_png_passes(self):
        validate_upload_image(upload("card.png"))

    def test_valid_webp_passes(self):
        from PIL import Image

        buffer = io.BytesIO()
        Image.new("RGB", (900, 600), (10, 120, 130)).save(buffer, format="WEBP")
        validate_upload_image(upload("card.webp", buffer.getvalue(), "image/webp"))

    def test_valid_jpeg_passes(self):
        from PIL import Image

        buffer = io.BytesIO()
        Image.new("RGB", (900, 600)).save(buffer, format="JPEG")
        validate_upload_image(upload("card.jpg", buffer.getvalue(), "image/jpeg"))

    def test_unknown_extension_rejected(self):
        with self.assertRaises(ValidationError):
            validate_upload_image(upload("logo.svg"))

    def test_wrong_content_with_image_extension_rejected(self):
        faked = SimpleUploadedFile("card.png", b"definitely not an image", "image/png")
        with self.assertRaises(ValidationError):
            validate_upload_image(faked)

    def test_decoded_but_unallowed_format_rejected(self):
        from PIL import Image

        buffer = io.BytesIO()
        Image.new("RGB", (400, 300)).save(buffer, format="GIF")
        with self.assertRaises(ValidationError):
            validate_upload_image(upload("card.png", buffer.getvalue(), "image/png"))

    def test_size_cap_is_setting_driven(self):
        with override_settings(UPLOAD_IMAGE_MAX_BYTES=10):
            with self.assertRaises(ValidationError):
                validate_upload_image(upload())  # valid PNG, exceeds the 10-byte cap

    # --- dimension cap (F-06 follow-up: resource hardening) --------------
    def test_dimension_cap_is_setting_driven(self):
        self.assertEqual(max_image_dimension(), 8000)

    def test_width_beyond_dimension_cap_rejected_before_decode(self):
        """A header declaring a wide image is rejected from header data
        alone — no pixels are ever decoded for an over-limit upload.
        """
        data = png_header_only_bytes(9000, 10)
        with override_settings(UPLOAD_IMAGE_MAX_DIMENSION=8000):
            with self.assertRaises(ValidationError):
                validate_upload_image(upload("card.png", data))

    def test_height_beyond_dimension_cap_rejected_before_decode(self):
        data = png_header_only_bytes(10, 9000)
        with override_settings(UPLOAD_IMAGE_MAX_DIMENSION=8000):
            with self.assertRaises(ValidationError):
                validate_upload_image(upload("card.png", data))

    def test_dimensions_within_cap_override_pass(self):
        image = upload("card.png", png_bytes(400, 300))
        self.assertEqual(
            validate_upload_image(image),
            [],
        )
        with override_settings(UPLOAD_IMAGE_MAX_DIMENSION=300):
            self.assertRaises(
                ValidationError, validate_upload_image, upload("card.png")
            )

    def test_custom_dimension_cap_enforced(self):
        """The guard honours a tight configured cap even when the image's
        natural dimensions sit far below the default 8000 px.
        """
        data = png_header_only_bytes(1200, 800)
        with override_settings(UPLOAD_IMAGE_MAX_DIMENSION=800):
            with self.assertRaises(ValidationError):
                validate_upload_image(upload("card.png", data))

        with override_settings(UPLOAD_IMAGE_MAX_DIMENSION=1200):
            warnings = validate_upload_image(
                upload("card.png", png_bytes(1200, 800)), warn_ratio="3/2"
            )
            self.assertEqual(warnings, [])  # exactly at the cap: accepted

    def test_truncated_image_rejected(self):
        """A decodable-format image whose data is cut off is rejected by the
        integrity pass (header parses, no complete pixel stream).
        """
        valid = png_bytes(100, 100)
        truncated = valid[: len(valid) - 30]
        with self.assertRaises(ValidationError):
            validate_upload_image(upload("card.png", truncated))

    def test_pillow_bomb_guard_surfaces_as_validation_error(self):
        """Pillow's own decompression-bomb safeguard stays enabled; when it
        fires the caller still sees a plain ValidationError (never a 500).
        """
        from unittest import mock
        from PIL import Image
        from PIL.Image import DecompressionBombError

        with mock.patch.object(Image, "open", side_effect=DecompressionBombError("x")):
            with self.assertRaises(ValidationError):
                validate_upload_image(upload())

    def test_no_file_bound_is_accepted(self):
        self.assertEqual(validate_upload_image(None), [])

    def test_narrow_section_image_warns_but_passes(self):
        warnings = validate_upload_image(
            upload("card.png", png_bytes(400, 400)),
            warn_width=SECTION_MIN_WIDTH,
            warn_ratio="3/2",
        )
        self.assertEqual(len(warnings), 2)  # width below minimum + ratio mismatch

    def test_wide_ratio_matching_image_has_no_warning(self):
        self.assertEqual(
            validate_upload_image(upload("card.png", png_bytes(1200, 800)), warn_ratio="3/2"),
            [],
        )

    def test_narrow_portrait_warns_but_passes(self):
        warnings = validate_upload_image(
            upload("profile.png", png_bytes(300, 600)), warn_width=PORTRAIT_MIN_WIDTH
        )
        self.assertEqual(len(warnings), 1)


class WebsiteSectionImageModelTests(TestCase):
    def test_str_and_defaults(self):
        row = WebsiteSectionImage.objects.create(key="home_hero", name="Homepage hero")
        self.assertEqual(str(row), "Homepage hero")
        self.assertTrue(row.is_active)
        self.assertFalse(bool(row.image))  # no file bound; filename stays empty

    def test_section_keys_are_stable_and_mapped(self):
        keys = {value for value, _label in SECTION_KEYS}
        self.assertEqual(
            keys,
            {
                "home_hero",
                "home_about",
                "auth_login_panel",
                "auth_register_panel",
                "doctors_listing_header",
                "doctor_profile_photo_aside",
                "specialities_mega_feature",
                "doctors_mega_feature",
            },
        )
        self.assertEqual(set(SECTION_STATIC_FALLBACKS), keys)
        for fallback in SECTION_STATIC_FALLBACKS.values():
            self.assertIn("static_path", fallback)

    def test_active_for_skips_inactive_and_imageless_rows(self):
        WebsiteSectionImage.objects.create(key="home_hero", name="Homepage hero")
        self.assertIsNone(WebsiteSectionImage.objects.active_for("home_hero"))

    def test_unknown_key_fails_validation(self):
        row = WebsiteSectionImage(key="not_a_key", name="Nope")
        with self.assertRaises(ValidationError):
            row.save()


class SectionImageTemplatetagTests(TestCase):
    """``section_image`` resolution: upload → static fallback → None."""

    def render(self, template_string, context=None):
        return Template(template_string).render(Context(context or {}))

    def test_unknown_key_fails_closed(self):
        out = self.render("{% load clinic_images %}{% section_image 'not_a_key' as p %}{{ p }}")
        self.assertEqual(out, "None")

    def test_fallback_used_when_no_upload(self):
        out = self.render("{% load clinic_images %}{% section_image 'home_hero' as p %}{{ p.url }}")
        self.assertIn("/static/img/home/hero-main.jpg", out)

    def test_fallback_flags_uploaded_false(self):
        out = self.render(
            "{% load clinic_images %}{% section_image 'auth_login_panel' as p %}"
            "{{ p.uploaded }}|{{ p.caption }}"
        )
        self.assertEqual(out.split("|")[0], "False")
        self.assertIn("Illustrative stock photograph", out)

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_uploaded_image_wins(self):
        row = WebsiteSectionImage.objects.create(
            key="home_hero", name="Homepage hero", image=upload()
        )
        out = self.render("{% load clinic_images %}{% section_image 'home_hero' as p %}{{ p.url }}")
        self.assertIn("/media/", out)
        self.assertIn(str(row.image.name), out)

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_inactive_row_falls_back_to_static(self):
        WebsiteSectionImage.objects.create(
            key="home_hero", name="Homepage hero", image=upload(), is_active=False
        )
        out = self.render("{% load clinic_images %}{% section_image 'home_hero' as p %}{{ p.url }}")
        self.assertIn("/static/img/home/hero-main.jpg", out)

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_uploaded_alt_and_caption_override_defaults(self):
        WebsiteSectionImage.objects.create(
            key="home_about",
            name="Homepage about band",
            image=upload("band.png"),
            alt_text="Uploaded alt for C1 verification",
            caption="Uploaded caption for C1 verification",
        )
        out = self.render(
            "{% load clinic_images %}{% section_image 'home_about' as p %}{{ p.alt }}|{{ p.caption }}"
        )
        self.assertIn("Uploaded alt for C1 verification", out)
        self.assertIn("Uploaded caption for C1 verification", out)

    def test_doctor_aside_caption_formats_the_doctor_name(self):
        doctor = make_doctor(make_speciality("Aside Spec"), "aside@example.com")
        out = self.render(
            "{% load clinic_images %}"
            "{% section_image 'doctor_profile_photo_aside' doctor=doctor as p %}{{ p.caption }}",
            {"doctor": doctor},
        )
        self.assertIn("not a photograph of Dr. Doc Smith", out)


class WebsiteSectionImageAdminTests(TestCase):
    """Administrator-only access and working upload flows through the admin."""

    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="root@example.com", password="S3cret-pass!"
        )
        self.admin = make_user("c1admin@example.com", User.Role.ADMIN, is_staff=True)

    def tearDown(self):
        for row in WebsiteSectionImage.objects.all():
            try:
                row.image.delete(save=False)
            except (OSError, ValueError):
                pass

    def test_section_model_is_registered_in_admin(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "Website section images")

    def test_administrator_role_without_superuser_can_use_the_registry(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("admin:website_websitesectionimage_changelist"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("admin:website_websitesectionimage_add"))
        self.assertEqual(response.status_code, 200)

    def test_plain_staff_cannot_reach_the_registry(self):
        staff = make_user("plain@example.com", User.Role.PATIENT, is_staff=True)
        self.client.force_login(staff)
        response = self.client.get(reverse("admin:website_websitesectionimage_changelist"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("admin:website_websitesectionimage_changelist"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response["Location"])

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_superuser_can_upload_a_section_image(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:website_websitesectionimage_add"))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("admin:website_websitesectionimage_add"),
            {
                "key": "home_hero",
                "name": "Homepage hero",
                "image": upload("hero.png"),
                "alt_text": "An illustrative clinic scene",
                "caption": "Illustrative image used for C1 verification",
                "is_active": "on",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        row = WebsiteSectionImage.objects.get(key="home_hero")
        self.assertTrue(row.image)
        # Uploads are scoped under MEDIA_ROOT and never near static/img.
        self.assertTrue(str(row.image.name).startswith("sections/home_hero/"))
        self.assertFalse(str(row.image.name).startswith("img/"))
        # The change page re-renders with the file preview available.
        response = self.client.get(
            reverse("admin:website_websitesectionimage_change", args=[row.pk])
        )
        self.assertContains(response, str(row.image.url))

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_admin_rejects_invalid_upload_with_form_error(self):
        self.client.force_login(self.superuser)
        faked = SimpleUploadedFile("thing.png", b"not really an image", "image/png")
        response = self.client.post(
            reverse("admin:website_websitesectionimage_add"),
            {"key": "home_about", "name": "Homepage about band", "image": faked},
        )
        self.assertEqual(response.status_code, 200)  # form re-rendered with errors
        self.assertContains(response, "errorlist")
        self.assertContains(response, "Upload a valid image")
        self.assertEqual(WebsiteSectionImage.objects.count(), 0)

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_admin_size_limit_blocks_oversized_upload(self):
        self.client.force_login(self.superuser)
        with override_settings(UPLOAD_IMAGE_MAX_BYTES=10):
            response = self.client.post(
                reverse("admin:website_websitesectionimage_add"),
                {"key": "home_about", "name": "Homepage about band", "image": upload()},
            )
        self.assertContains(response, "too large", status_code=200)
        self.assertEqual(WebsiteSectionImage.objects.count(), 0)

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_speciality_admin_upload_saves_and_previews(self):
        self.client.force_login(self.superuser)
        speciality = make_speciality("Imagery Admin Spec")
        add_url = reverse("admin:clinic_speciality_add")
        response = self.client.get(add_url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            add_url,
            {
                "name": "Imagery Admin Spec 2",
                "slug": "imagery-admin-spec-2",
                "description": "",
                "image_caption": "Illustrative tile used for C1 verification",
                "image": upload("card.png"),
                "is_active": "on",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        spec = Speciality.objects.get(slug="imagery-admin-spec-2")
        self.assertTrue(spec.image)
        self.assertTrue(str(spec.image.name).startswith("specialities/"))
        self.assertFalse(str(spec.image.name).startswith("img/"))
        self.assertEqual(spec.image_caption, "Illustrative tile used for C1 verification")
        response = self.client.get(
            reverse("admin:clinic_speciality_change", args=[spec.pk])
        )
        self.assertContains(response, "Current image")
        self.assertContains(response, str(spec.image.url))

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_doctor_admin_change_page_shows_portrait_preview(self):
        self.client.force_login(self.superuser)
        doctor = make_doctor(make_speciality("Portrait Admin Spec"), "portadm@example.com")
        response = self.client.get(reverse("admin:clinic_doctor_change", args=[doctor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Current portrait")
        self.assertContains(response, "No portrait uploaded")

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_doctor_upload_path_never_enters_static(self):
        doctor = make_doctor(make_speciality("Upload Path Spec"), "uppath@example.com")
        doctor.profile_image = upload("portrait.png")
        doctor.save()
        self.assertTrue(str(doctor.profile_image.name).startswith("doctors/"))
        self.assertFalse(str(doctor.profile_image.name).startswith("img/"))
        doctor.profile_image.delete(save=False)


class SectionImageMediaServingTests(TestCase):
    """Development media serving is wired DEBUG-only in ``config/urls.py``.

    The Django test runner forces DEBUG=False, so the two halves of this
    contract are asserted by rebuilding ``config.urls`` under each mode.
    """

    def test_dev_setting_registers_media_route(self):
        import importlib

        import config.urls as root_urls

        with override_settings(DEBUG=True):
            importlib.reload(root_urls)
            routes = [p for p in root_urls.urlpatterns if "media" in str(p.pattern)]
        importlib.reload(root_urls)  # restore DEBUG=False wiring
        self.assertTrue(routes)
        self.assertIs(routes[0].callback, serve)

    def test_prod_setting_registers_no_media_route(self):
        # Django's test runner runs with DEBUG=False — production mode —
        # so: no media route is registered at all.
        import importlib

        import config.urls as root_urls

        importlib.reload(root_urls)
        self.assertEqual(
            [p for p in root_urls.urlpatterns if "media" in str(p.pattern)], []
        )

    def test_static_fallback_rendering_unchanged_without_uploads(self):
        speciality = Speciality.objects.create(
            name="Fallback Unchanged Spec", slug="cardiology"
        )
        response = self.client.get(reverse("speciality_detail", args=[speciality.slug]))
        self.assertContains(response, "/static/img/specialities/cardiology-card.jpg")
        self.assertContains(response, "Illustrative stock photo")


class UploadedImageRenderingTests(TestCase):
    """Fallback vs uploaded rendering over the real templates."""

    @classmethod
    def setUpTestData(cls):
        cls.doctor = make_doctor(make_speciality("Imagery Doc Spec"), "imdoc@example.com")

    def test_home_uses_static_fallback_without_upload(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "/static/img/home/hero-main.jpg")
        self.assertContains(response, "Illustrative stock photo")

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_home_uses_uploaded_hero_and_about_shot(self):
        hero = WebsiteSectionImage.objects.create(
            key="home_hero", name="Homepage hero", image=upload()
        )
        about = WebsiteSectionImage.objects.create(
            key="home_about",
            name="Homepage about band",
            image=upload("band.png"),
            caption="Uploaded about caption for C1 verification",
        )
        response = self.client.get(reverse("home"))
        self.assertContains(response, str(hero.image.name))
        self.assertContains(response, str(about.image.name))
        self.assertContains(response, "Uploaded about caption for C1 verification")
        # The about band's static fallback honesty copy is gone for this section.
        self.assertNotContains(response, "calm clinic consultation room")

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_speciality_upload_renders_with_caption_and_fallback_clears_exactly(self):
        speciality = Speciality.objects.create(
            name="Imagery Clear Fallback Spec", slug="cardiology"
        )
        speciality.image = upload("spec.png")
        speciality.image_caption = "Illustrative imagery test upload"
        speciality.save()
        response = self.client.get(reverse("speciality_detail", args=[speciality.slug]))
        self.assertContains(response, "/media/")
        self.assertContains(response, "Illustrative imagery test upload")
        # Removing the upload restores the documented static rendering.
        speciality.image = None
        speciality.save()
        response = self.client.get(reverse("speciality_detail", args=[speciality.slug]))
        self.assertContains(response, "/static/img/specialities/")
        self.assertNotContains(response, "/media/")

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_doctor_portrait_upload_and_clearing(self):
        self.doctor.profile_image = upload("portrait.png")
        self.doctor.save()
        response = self.client.get(reverse("doctor_detail", args=[self.doctor.slug]))
        self.assertContains(response, "/media/")
        self.assertContains(response, str(self.doctor.profile_image.name))
        # The aside keeps its honesty caption, independent of the portrait.
        self.assertContains(response, "not a photograph of Dr.")
        self.doctor.profile_image = None
        self.doctor.save()
        response = self.client.get(reverse("doctor_detail", args=[self.doctor.slug]))
        self.assertNotContains(response, "/media/")

    @override_settings(MEDIA_ROOT=_TEMP_MEDIA_ROOT)
    def test_login_and_register_panels_respect_section_uploads(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertContains(response, "/static/img/home/hero-main.jpg")
        row = WebsiteSectionImage.objects.create(
            key="auth_login_panel", name="Login visual panel", image=upload("login.png")
        )
        response = self.client.get(reverse("accounts:login"))
        # The login visual panel itself switched to the upload (the shared
        # navigation's mega-image still denotes its own section).
        self.assertContains(response, str(row.image.name))
        response = self.client.get(reverse("accounts:register"))
        # Register panel falls back to its own documented static image.
        self.assertContains(response, "/static/img/about/waiting-area.jpg")


class ContactPageTests(TestCase):
    """Public /contact/ page: static template, no models, no form."""

    def test_contact_ok_for_anonymous(self):
        response = self.client.get(reverse("contact"))
        self.assertEqual(response.status_code, 200)

    def test_contact_uses_correct_template(self):
        response = self.client.get(reverse("contact"))
        self.assertTemplateUsed(response, "website/contact.html")
        self.assertTemplateUsed(response, "base.html")

    def test_contact_page_title_headings_and_content(self):
        response = self.client.get(reverse("contact"))
        self.assertContains(response, "<title>Contact — Care_Clinic</title>")
        self.assertContains(response, "<h1>")
        self.assertContains(response, "Book an appointment")

    def test_contact_links_resolve(self):
        response = self.client.get(reverse("contact"))
        content = response.content.decode()
        self.assertIn(reverse("doctor_list"), content)
        self.assertIn(reverse("faq"), content)

    def test_contact_footer_links_resolve(self):
        response = self.client.get(reverse("contact"))
        content = response.content.decode()
        self.assertIn('href="/contact/"', content)
        self.assertIn('href="/faq/"', content)

    def test_contact_visible_when_signed_in(self):
        User.objects.create_user(
            email="signedin@example.com",
            password="S3cret-pass!",
            role=User.Role.PATIENT,
        )
        self.client.force_login(User.objects.get(email="signedin@example.com"))
        self.assertEqual(self.client.get(reverse("contact")).status_code, 200)

    def test_contact_no_form_posted(self):
        response = self.client.get(reverse("contact"))
        self.assertNotContains(response, "<form")


class FaqPageTests(TestCase):
    """Public /faq/ page: static template, answers mirror actual behavior."""

    def test_faq_ok_for_anonymous(self):
        response = self.client.get(reverse("faq"))
        self.assertEqual(response.status_code, 200)

    def test_faq_uses_correct_template(self):
        response = self.client.get(reverse("faq"))
        self.assertTemplateUsed(response, "website/faq.html")
        self.assertTemplateUsed(response, "base.html")

    def test_faq_page_title_and_headings(self):
        response = self.client.get(reverse("faq"))
        self.assertContains(response, "<title>FAQ — Care_Clinic</title>")
        self.assertContains(response, "<h1>Frequently asked questions</h1>")

    def test_faq_answers_match_actual_behavior(self):
        response = self.client.get(reverse("faq"))
        content = response.content.decode()
        self.assertIn("CC-2026-000123", content)  # real reference format
        self.assertIn("24 hours", content)  # CANCELLATION_WINDOW = 24 h
        self.assertContains(response, "password")

    def test_faq_resolves_named_route(self):
        self.assertEqual(reverse("faq"), "/faq/")

    def test_faq_visible_when_signed_in(self):
        user = User.objects.create_user(
            email="faquser@example.com",
            password="S3cret-pass!",
            role=User.Role.PATIENT,
        )
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("faq")).status_code, 200)


class ContactFaqNavigationTests(TestCase):
    """Links to the new pages resolve and only add lightweight routes."""

    def test_base_footer_has_contact_and_faq(self):
        response = self.client.get(reverse("home"))
        content = response.content.decode()
        self.assertIn('href="/contact/"', content)
        self.assertIn('href="/faq/"', content)

    def test_urls_resolve_to_expected_views(self):
        self.assertEqual(resolve("/contact/").view_name, "contact")
        self.assertEqual(resolve("/faq/").view_name, "faq")


class DemoImageryStaticTests(TestCase):
    """Batch-4 static assets: every demo speciality/doctor resolves its file.

    Fallback behavior is untouched: the helpers still return "" for unknown
    slugs (the initials avatar renders instead) and the manifest must still
    document every new raster file.
    """

    NEW_SLUGS = {
        "speciality": ("neurology", "ear-nose-throat", "ophthalmology", "gynaecology"),
        "doctor": (
            "sabari",
            "prabhakaran",
            "sanjay-krishna",
            "radha-krishnan",
            "swetha",
        ),
    }
    MANIFEST = Path(__file__).resolve().parents[1] / "docs" / "imagery-licensing.md"

    @classmethod
    def setUpTestData(cls):
        call_command("seed_clinic")

    def test_speciality_detail_renders_expected_tile(self):
        for slug in self.NEW_SLUGS["speciality"]:
            speciality = Speciality.objects.get(slug=slug)
            response = self.client.get(speciality.get_absolute_url())
            with self.subTest(slug=slug):
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    f"/static/img/specialities/{slug}-card.jpg",
                    msg_prefix=slug,
                )

    def test_doctor_detail_renders_expected_portrait(self):
        for slug in self.NEW_SLUGS["doctor"]:
            doctor = Doctor.objects.get(slug=slug)
            response = self.client.get(doctor.get_absolute_url())
            with self.subTest(slug=slug):
                self.assertEqual(response.status_code, 200)
                self.assertContains(
                    response,
                    f"/static/img/doctors/{slug}-profile.webp",
                    msg_prefix=slug,
                )

    def test_portrait_files_are_all_distinct(self):
        digests = set()
        import hashlib

        base = Path(__file__).resolve().parents[1] / "static" / "img" / "doctors"
        for slug in self.NEW_SLUGS["doctor"]:
            data = (base / f"{slug}-profile.webp").read_bytes()
            digests.add(hashlib.sha256(data).hexdigest())
        self.assertEqual(len(digests), 5)

    def test_initials_avatar_fallback_survives(self):
        spec = Speciality.objects.get(slug="neurology")
        user = User.objects.create_user(
            email="noimage@example.com",
            password="S3cret-pass!",
            role=User.Role.DOCTOR,
            first_name="Noor",
        )
        doctor = Doctor.objects.create(
            user=user,
            speciality=spec,
            registration_number="REG-IMG-FALLBACK",
            qualification="MBBS",
        )
        response = self.client.get(doctor.get_absolute_url())
        # No static file for the in-test slug: the initials avatar renders
        # here instead (other demo doctors' portraits still resolve elsewhere).
        self.assertNotContains(response, "/img/doctors/noor-profile.webp")
        self.assertNotContains(response, "static/img/doctors/noor-profile.webp")
        self.assertContains(response, "avatar--xl")
        self.assertContains(response, ">N")

    def check_manifest_covers(self, filenames):
        text = self.MANIFEST.read_text(encoding="utf-8")
        for name in filenames:
            self.assertIn(name, text)

    def test_manifest_documents_every_new_raster_image(self):
        self.check_manifest_covers(
            [f"static/img/specialities/{s}-card.jpg" for s in self.NEW_SLUGS["speciality"]]
            + [f"static/img/doctors/{d}-profile.webp" for d in self.NEW_SLUGS["doctor"]]
        )

    def test_manifest_records_pexels_licence_and_photographers(self):
        text = self.MANIFEST.read_text(encoding="utf-8")
        for photographer in (
            "Anna Shvets",
            "Karolina Grabowska",
            "Antoni Shkraba",
            "MART PRODUCTION",
            "Daniil Kondrashin",
            "Tima Miroshnichenko",
            "Layth Mushreq",
            "Oys Photography",
            "KAWENY DENYELE",
        ):
            self.assertIn(photographer, text)
        self.assertIn("pexels.com/license", text)
