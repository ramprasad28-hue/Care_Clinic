# Phase C1 — Admin-Managed Website Imagery: Delivery Report

**Status:** Implementation complete — all gates green — **user reviewed and
signed off (2026-10-20)**; committed to `origin/main` as `4e0754f`
("feat: complete clinic frontend and admin-managed imagery").
**Date:** 2026-10-20 · **Plan:** `docs/phase-c1-admin-managed-imagery-plan.md` ·
**Decision:** ADR-022 (`docs/decisions.md`) — supersedes ADR-015 (per user
approval of that decision when C1 was scheduled).

---

## 1. What was built

Administrator-only upload, replace, preview and management of website imagery
through Django Admin, with the serving decision deferred to the web-server
layer. Nothing in `static/`, template markup, CSS or JS is modified by the
feature's existence; the site renders byte-identically to the approved F6 build
until an upload exists.

### 1a. Models, migrations, storage

- `clinic.Speciality.image` (`ImageField`, nullable/blank, keep honest
  `image_caption`, max_length 255) + `clinic.Speciality.image_caption`.
- `clinic.Doctor.profile_image` + `profile_image_caption` (fulfils the planned
  field in data-model §3.4; reverses ADR-015).
- New `website.WebsiteSectionImage` registry model (`key` slug unique with the
  8 stable `SECTION_KEYS`, `name` unique, `image`, `alt_text`, `caption`,
  `is_active`, `updated_at`). `save()` runs `full_clean()`, so an unknown key
  fails even through a raw ORM insert. `active_for(key)` resolves the active
  row **with a bound upload** for a section; `SECTION_STATIC_FALLBACKS` maps
  every key to the exact static file/alt/caption used by the F6 rendering.
- `upload_to` callables scope uploads to
  `specialities/<slug>/card.<ext>`, `doctors/<slug>/profile.<ext>`,
  `sections/<key>/image.<ext>` — uploads can never reach `static/img/`
  (enforced by tests too).
- Migrations: `clinic/migrations/0002_doctor_profile_image_doctor_profile_image_caption_and_more.py`,
  `website/migrations/0001_initial.py`. Applied to the dev sqlite DB;
  `makemigrations --check --dry-run` reports no drift.
- Pillow 11.3.0 installed; `requirements.txt` gains
  `Pillow>=10.0,<12.0` (backend-only parsing/validation dependency).
- `config/urls.py` serves `MEDIA_URL` **DEBUG-only** (checked in both the
  production and development modes by tests). Production serving is a
  deployment decision (`MEDIA_URL` currently `"/media/"`, `MEDIA_ROOT` = repo
  `media/`, which is and stays git-excluded via `/media/` so uploads never
  enter source control).

### 1b. Validation (`website/image_validation.py`)

Shared module used by all three models/admin forms (no Django model imports —
no cycles):

- Extension allowlist (`.jpg/.jpeg/.png/.webp`) **and** the file must decode
  via Pillow into `JPEG`/`PNG`/`WebP` (GIF/BMP content rejected even when
  named `.png`; `.svg` rejected outright for its scriptable content).
- Size cap from `UPLOAD_IMAGE_MAX_BYTES` (default 2 MiB).
- Dimension/ratio guidance is **warnings-only** (admin warning messages after a
  successful save): portraits warn below 480 px width; section slots warn below
  900 px and when the ratio deviates ≥ 0.35 from the editorial 3:2 — never
  rejected (valid image with a different crop is still valid data).
- The default cap value, setting-driven cap override, and all rejection paths
  have standalone tests.

### 1c. Django Admin

- `SpecialityAdmin` / `DoctorAdmin` gain `ImageWarningAdminMixin`,
  content-validated admin forms, a changelist thumbnail (`image_thumb` /
  `portrait_thumb`) and a readonly "Current image / Current portrait" preview,
  with a "No image uploaded — static fallback shown" state in time.
  Pre-existing fieldsets/lists preserved; the C1 note is plain.
- New `WebsiteSectionImageAdmin` (Website app): administrator-only (reuses
  `AdministratorOnlyMixin`/`ImageWarningAdminMixin`/`_media_src` from
  `clinic.admin` — one source of truth), with a grouped edit form
  (`image_preview`, upload, alt, fine caption, `is_active`) and a thumbnail
  changelist filterable by section key and active state.

### 1d. Template layer

- `website/templatetags/clinic_images.py` rewritten: tags return **ready-to-use
  URLs** (callers never wrap in a second `{% static %}`):
  - `doctor_portrait(doctor)` — upload URL, or slug-mapped static webp probe,
    or `""` (initials avatar fallback);
  - `speciality_tile_image(speciality)` — upload URL, or slug-mapped static
    jpg probe, or `""`;
  - `section_image(key, doctor=None)` — new; upload row first, else static
    fallback **only if that file exists**, else `None` (fails closed for
    unknown keys). Merges registry `alt_text`/`caption` over fallback defaults
    and formats `{doctor_name}` in the apart-aside honesty caption.
- `static_exists` retained for any non-image probes.
- **11 consumer templates updated to the ready-to-use URLs with conditional
  guards** — a missing file never emits a broken `<img>`; the same CSS
  `object-fit: cover` aspect boxes correct any upload's aspect without
  distortion or layout shift: `_speciality_card.html`, `_doctor_card.html`,
  `_nav_mega_panel.html`, `_nav_doctors_panel.html`, `home.html`,
  `speciality_detail.html`, `doctor_detail.html`, `doctor_list.html`,
  `accounts/login.html`, `accounts/register.html`,
  `dashboards/doctor_dashboard.html`,
  `appointment_book/detail/reschedule.html`.
- Honesty captions preserved: static fallbacks keep their "Illustrative stock
  photo — not a photograph of Dr. {doctor_name}." / "not a Care_Clinic
  premises" wording; an uploaded row can override its caption (or leave it to
  the default).

## 2. Tests (all new, C1)

In `website/tests.py` (64 tests in the app, covering the C1 surfaces end to end):

- `UploadImageValidationTests` — real JPEG/PNG/WebP bytes (PIL-generated),
  SVG/GIF/text content rejection, size cap default + setting override,
  dimension/ratio warning policy.
- `WebsiteSectionImageModelTests` — key domain stability, fallback mapping,
  `active_for` skipping inactive/image-less rows, unknown-key `save()` failure.
- `SectionImageTemplatetagTests` — fails-closed unknown key, static fallback
  upload wins, `uploaded` flag, alt/caption override, `{doctor_name}` caption
  formatting.
- `WebsiteSectionImageAdminTests` — superuser AND plain ADMIN-role staff can
  admin the registry; plain `is_staff` (non-ADMIN) gets 403; anonymous is
  redirected; successful end-to-end upload POST; invalid upload re-renders the
  admin form with an errorlist; size cap blocks oversized POST; speciality
  admin end-to-end upload + preview; doctor admin preview/settings surface;
  upload paths never under `img/`. (Admin login mechanics and the doctor-owned
  RBAC rules remain covered by the pre-existing `AdminAuthorizationTests` in
  `clinic/tests.py`; the new tests cover only the imagery surfaces and the
  ADMIN-module gating.)
- `SectionImageMediaServingTests` — DEBUG=True media routes registered
  (`django.views.static.serve`), DEBUG=False route absent; static fallback
  rendering equals the long-standing "Illustrative stock photo" identity.
- `UploadedImageRenderingTests` — home/speciality/doctor/auth surfaces:
  fallback rendering without uploads (identical to F6), upload rendering with
  captions, and **upload-clear → fallback restoration** round-trips.

`clinic/tests.py` (47 tests) unchanged and green at full-suite level —
existing admin/RBAC suites cover the shared acccess-control model that C1
reuses.

## 3. Gates (final, run after all edits)

| Gate | Result |
|---|---|
| `manage.py test --parallel 1` | **271 tests OK** (1 pre-existing skip; previously 230 → 41 added across both apps' suites) |
| `manage.py check` | 0 issues |
| `manage.py makemigrations --check --dry-run` | no changes |
| `git diff --check` | clean (0 rc) |

## 4. Visual verification (post-live-server, `--noreload` restart pattern)

Seeded uploads (dev DB, later removed): all 8 registry sections got copies of
the documented licensed Pexels stock for their atmosphere slots; Cardiology got
its licensed card asset; the demo portrait is a **neutral PIL-generated
abstract placeholder** (a stock photo would never be acceptable for a person's
portrait band). Screenshots in `%TEMP%\opencode\phase-c1\shots\`:

| Surface | 1440 | 390 |
|---|---|---|
| Homepage (hero upload) | ✅ `c1_home_1440.png` | ✅ `c1_home_390.png` |
| Doctor detail (uploaded portrait + aside) | ✅ `c1_doctor_portrait_1440.png` | — |
| Speciality detail (uploaded tile) | ✅ `c1_speciality_1440.png` | — |
| Doctors listing (hero band upload) | ✅ `c1_doctor_list_1440.png` | — |
| Login (panel upload) | ✅ `c1_login_1440.png` | — |
| Register (panel upload) | ✅ `c1_register_1440.png` | — |
| Admin: section-image registry | ✅ `c1_admin_section_images_1440.png` | — |
| Admin: speciality change form (preview/upload/replace) | ✅ `c1_admin_speciality_change_1440.png` | — |
| Admin: doctor list (portrait thumb) | ✅ `c1_admin_doctor_list_1440.png` | — |
| **Fallbacks (uploads cleared)** — homepage | ✅ `c1_fallback_home_1440.png` | ✅ `c1_fallback_home_390.png` |

Findings: no horizontal overflow at either viewport; no broken-image state in
bold assertions (`heroMain`, `mediaLeft` checks; fallback renders exactly the
pre-C1 static set and no `/media/` URLs remain once uploads are cleared); the
admin UI's "Currently/Clear/Current image" behaviour renders as expected;
0 additional CSS/CL issues introduced.

## 5. Housekeeping (restored to baseline)

- All demo uploads + the temporary QA superuser (`c1qa`) deleted; dev DB has
  6 users, 0 registry rows, `media/` empty as before.
- Dev server processes stopped (no runserver left running).

## 6. Git accounting

- Working-tree porcelain entries: **85 → 98** (85 at C1 start, after F6 — 96
  at code-complete, +2 for this report and the docs updates; final = 98). C1
  neither staged nor committed anything — new untracked C1 sources are
  `website/admin.py`, `website/forms.py`, `website/image_validation.py`,
  `website/models.py`, `website/migrations/`, `website/templatetags/`,
  `clinic/migrations/0002_*.py`, `docs/phase-c1-admin-managed-imagery-report.md`,
  plus the modified C1 files listed in §7.
- Nothing staged/committed/pushed; no submodule or lockfile changes beyond
  `requirements.txt` (line-endings kept per repo config).

## 7. Files changed by this phase

**New:** `website/image_validation.py`, `website/models.py`, `website/forms.py`,
`website/admin.py`, `website/migrations/0001_initial.py`,
`website/templatetags/clinic_images.py`,
`clinic/migrations/0002_doctor_profile_image_doctor_profile_image_caption_and_more.py`,
`docs/phase-c1-admin-managed-imagery-report.md` (this file).

**Modified:** `clinic/models.py`, `clinic/admin.py`, `clinic/forms.py`,
`website/tests.py`, `config/urls.py`, 11 consumer templates (§1d),
`requirements.txt`, docs (`decisions.md`, `data-model.md`,
`imagery-licensing.md`, `implementation-roadmap.md`).

## 8. Limitations / open decisions (deferred)

1. **Production media serving** is a deployment decision (web server or object
   storage in front of `MEDIA_ROOT`);
   code enforces that Django never serves media when `DEBUG=False`.
2. **Dimension/ratio policy** is warning-only by design; if the employer wants
   hard rejections for specific surfaces, that is a setting delta in
   `website/image_validation.py`.
3. **Real imagery sourcing/licensing** remains a human administrative duty
   (§2 duty list in `docs/imagery-licensing.md`): the code cannot certify
   licence provenance for upload content.
4. The hero/about/auth-section uploads are atmosphere slots — their captions
   may be admin-overridden freely; only the portrait/aside surfaces carry the
   per-doctor honesty caption and it is kept when uploaded via the section
   key (the default wording is not offered for editing here).

## 9. STOP status

Per the standing directive: C1 implementation, tests, gates and visual
verification are complete; docs (ADR-022, data-model, imagery licensing
duties, roadmap) are updated. **No B0+ work started.**
The user reviewed this report and approved the implementation (2026-10-20);
the approved work is committed to `origin/main` as `4e0754f`. All technical
findings and deployment limitations in this report remain unchanged.
