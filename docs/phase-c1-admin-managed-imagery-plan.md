# Phase C1 — Admin-Managed Website Imagery

**Status (2026-10-20):** ✅ **Implemented** (this document is the approved plan,
preserved as written; findings/results live in
`docs/phase-c1-admin-managed-imagery-report.md`). Original planning note: no
application code, models, admin classes, templates, CSS,
JavaScript, settings, assets, or migrations were changed for this document.
**Position in roadmap:** after **F6 (Full frontend QA — final approval)** and before the
backend-polishing phases (B0+). The frontend-first order (F-before-B) was explicitly
requested by the user and is preserved: the requirement itself was gathered while F4 was in
review so that F5/F6 could proceed unblocked.

---

## 0. Origin of the requirement

User directive (2026-10-20): *the administrator must be able to upload, replace, preview and
manage website images through Django Admin without editing templates, CSS, JavaScript, or
files inside source-controlled `static/`.* F5 (dashboards) and F6 (final frontend QA)
remain ahead of it; C1 is scheduled immediately after F6.

## 1. Current state (inspected, 2026-10-20)

- **All imagery is static-path driven.** A `static_exists` filter plus a `doctor_portrait`
  template tag (`website/templatetags/clinic_images.py`) filesystem-probe names under
  `STATICFILES_DIRS`/`STATIC_ROOT`; a missing file degrades gracefully (no broken `<img>`).
- **Settings** (`config/settings/base.py:89-94`) already define `MEDIA_URL = "/media/"` and
  `MEDIA_ROOT = BASE_DIR / "media"`, but the `media/` directory does not exist,
  `/media/` is **not served** in `config/urls.py` (there is no `static()`/`media()` serving
  block even in DEBUG), and no code or model references MEDIA settings today.
- **No Pillow** in `requirements.txt`; ADR-015 deliberately kept it out (see §3).
- **Image usage inventory (actual templates):**

| Surface | File | Image mapping |
|---|---|---|
| Homepage hero | `templates/home.html:11` | `img/home/hero-main.jpg` |
| Homepage about band | `templates/home.html:91` | `img/about/waiting-area.jpg` |
| Speciality card tile | `templates/partials/_speciality_card.html` (home + listing) | `img/specialities/<slug>-card.jpg` |
| Specialities mega-menu tiles | `templates/partials/_nav_mega_panel.html` | `img/specialities/<slug>-card.jpg` |
| Specialities mega-menu feature | `_nav_mega_panel.html:27` | `img/about/waiting-area.jpg` |
| Doctor card portrait | `templates/partials/_doctor_card.html` (home/list/detail) + `_nav_doctors_panel.html` | `img/doctors/<slug>-profile.webp` via `doctor_portrait` |
| Doctors mega-menu feature | `_nav_doctors_panel.html:28` | `img/home/hero-main.jpg` |
| Speciality detail page-hero | `website/speciality_detail.html:8` | `img/specialities/<slug>-card.jpg` |
| Doctor listing header | `website/doctor_list.html:22` | `img/about/waiting-area.jpg` |
| Doctor detail aside photo | `website/doctor_detail.html:87` | `img/home/hero-main.jpg` (captioned "not a photograph of Dr. {name}") |
| Login visual panel | `accounts/login.html:12` | `img/home/hero-main.jpg` |
| Register visual panel | `accounts/register.html:12` | `img/about/waiting-area.jpg` |

- **Django Admin** (`clinic/admin.py`): `SpecialityAdmin`/`DoctorAdmin` already exist and are
  `AdministratorOnlyMixin`-gated (ADMIN role or superuser). No image fields yet. No
  `website/admin.py` exists (the website app has no models).
- **`docs/data-model.md` §3.4** already anticipated `Doctor.profile_image` (image, nullable)
  — the field was described in the approved data model but deliberately not implemented
  (ADR-015). C1 reconciles the two.
- **Licensing:** all current images are documented in `docs/imagery-licensing.md` (Pexels
  batch 1 + demo-portrait batch 2), with strict honesty rules:
  stock is **never** presented as a real clinic doctor/premises; demo portraits are
  slug-mapped placeholders that one-for-one replacement will make real.

## 2. Scope

### A. Speciality images

- `Speciality` gains an uploaded, administrator-editable image.
- The same image feeds **every current consumer of the per-slug convention**: homepage and
  listing cards (`_speciality_card.html`), specialities mega-menu tiles, and the speciality
  detail page-hero.
- Upload replaces the static `<slug>-card.jpg` lookup only for that speciality; specialities
  with no upload keep the existing text-only / static-file fallback, and a deleted upload
  must degrade exactly as a missing file does today.
- Alt text stays optional (tiles are decorative, `alt=""`, title carries meaning); a caption
  field is optional for the detail page-hero ("Illustrative stock photo"), required to keep
  the existing honesty captions truthful.

### B. Doctor portraits

- `Doctor` gains an administrator-managed profile image — **this reverses the previous
  architecture decision not to implement `Doctor.profile_image`** (ADR-015 → see §3 and the
  new ADR in `docs/decisions.md`).
- The same portrait is used consistently on doctor cards (homepage, listing, speciality
  detail), the doctor detail masthead, the Doctors mega menu, and the F4 booking/reschedule/
  detail strips — i.e. every existing consumer of `doctor_portrait`.
- **Fallback preserved:** the initials avatar remains the fallback whenever no upload exists
  (and for any error case). Resolution order: admin upload → initial avatar.
- **Honesty rule (non-negotiable):** a generic stock photograph must never be presented as a
  real doctor's portrait. The existing slug-mapped static demo portraits stay labelled as
  demo placeholders while they remain the source of truth; once the admin uploads a
  portrait, it is presumed a genuine, consented photograph of that doctor (the admin
  workflow must respect the licensing/consent guidance in `docs/imagery-licensing.md` §batch
  2). The "not a photograph of Dr. {name}" caption on `doctor_detail`'s aside applies to the
  static supporting image only — it must never be attached to an admin-uploaded portrait.

### C. Website section-image registry (new model)

A Django Admin-managed registry replaces the fixed section mappings above. Proposed model
`website.WebsiteSectionImage` (the `website` app already owns public pages, its templatetags,
and no models today — adding them introduces the app's **first migration**):

| Field | Type | Notes |
|---|---|---|
| `key` | unique slug, choices from a `SECTION_KEYS` constant | stable identifiers, never content-derived |
| `name` | unique varchar(120) | human-readable label for the admin UI ("Homepage hero") |
| `image` | `ImageField`, nullable | optional so a section can be unset |
| `alt_text` | varchar(255), blank | required when the section is content-bearing; decorative sections leave it empty |
| `caption` | varchar(255), blank optional | honest-caption slot where templates show one |
| `is_active` | bool, default True | inactive → revert to static fallback |
| `updated_at` | auto | audit |

Proposed stable keys (sections that **exist today**; no invented routes/sections):

| Key | Feeds | Current fallback |
|---|---|---|
| `home_hero` | Homepage hero photograph | `img/home/hero-main.jpg` |
| `home_about` | Homepage About band figure plate | `img/about/waiting-area.jpg` |
| `auth_login_panel` | Login visual panel | `img/home/hero-main.jpg` |
| `auth_register_panel` | Register visual panel | `img/about/waiting-area.jpg` |
| `doctors_listing_header` | Doctor listing editorial header | `img/about/waiting-area.jpg` |
| `doctor_profile_photo_aside` | Doctor detail aside supporting photo | `img/home/hero-main.jpg` |
| `specialities_mega_feature` | Specialities mega-menu feature | `img/about/waiting-area.jpg` |
| `doctors_mega_feature` | Doctors mega-menu feature | `img/home/hero-main.jpg` |

The speciality listing (`website/speciality_list.html`) is currently text-led with no image —
it is **not** given one (do not create image-led sections that do not exist). New keys can be
appended to the constant later; the template tag fails closed (empty) for unknown keys.

### D. Optional supporting visuals

- Search for booking-area/dashboard imagery may be revisited during implementation.
- **Constraint:** no imagery inside appointment tables, forms, or individual appointment
  records, and no per-appointment images. Any addition stays a section-key-level registry
  entry (e.g. a booking-page supporting visual), evaluated against honesty/CLS rules.

## 3. Technical requirements

### Models & migrations (prepared in C1; migrations are built, not applied, when the phase is implemented)

1. `clinic.Speciality`: add nullable `image` (`ImageField`, `upload_to="specialities/"`,
   blank=True) — additive; existing specialities remain `NULL` → present behaviour preserved.
2. `clinic.Doctor`: add nullable `profile_image` (`ImageField`, `upload_to="doctors/"`,
   blank=True) — **supersedes ADR-015**; existing doctors keep initials avatars.
3. `website.WebsiteSectionImage`: new model as in §2C (first `website` migration).
4. One migration per app (`clinic`, `website`); no data migration required because every
   consumer falls back to the current static mappings — the existing static inventory keeps
   working untouched until an admin uploads replacements.

### Upload path & file safety

- `MEDIA_ROOT` (`BASE_DIR / media`) is separate from `static/img/` (version-controlled) —
  admin uploads can never overwrite source-controlled assets or static naming conventions.
- Upload-path callable keeps date-hierarchies out but scopes per kind
  (`doctors/<doctor.slug>/profile<ext>` collisions resolved by Django's uniquifier).
- Server-side validation in form/model `clean()`:
  - allowlist `jpg/jpeg/png/webp` (SVG rejected: scriptable content);
  - Pillow `Image.open` decode (replaces relying on extension alone);
  - size cap (~2 MB, setting-driven constant), and dimension guidance
    (portrait ≥ 600px wide; section/hero ≥ 1200px wide) enforced as validation errors;
  - re-orientation is handled by the browser via `object-fit` — no post-processing pipeline
    in v1 (deliberate scope limit).
- **Pillow is added to `requirements.txt`** (reversing ADR-015's no-Pillow consequence).
  Django validates image fields with Pillow already when the dependency is present.

### Admin experience & access control

- `SpecialityAdmin`/`DoctorAdmin` gain `ImageFieldFormWidget` fields with admin previews
  (`clearable file input` + current-image preview markup; a small admin `readonly`/`formfield_overrides`
  approach or a tiny admin mixin — hand-rolled, no new admin dependency).
- New `website/admin.py`: `WebsiteSectionImageAdmin` registered under the same
  administrator-only rules as the clinic admin (reuse/extend `AdministratorOnlyMixin` or
  mirror its checks); list view = key, name, active, preview thumbnail; edit = preview,
  alt text, caption.
- Non-staff users can never reach any of it (Django admin requires `is_staff`; RBAC matrix:
  site images are business assets — administrator-only, matching "Manage doctors /
  specialities" rows in `architecture.md` §6).
- Deleting an image in admin must not dangling-reference the media file; model choice for v1:
  keep the stored file (recoverable), rely on the fallback chain for presentation.

### Serving & deployment

- `config/urls.py` (DEBUG only): serve `MEDIA_ROOT` via `static()` — standard development
  serving; production precedence documented (web server / persistent volume), never
  DEBUG-gated in prod settings.
- `MEDIA_URL`/`MEDIA_ROOT` already exist in `base.py`; verify in both `development.py` and
  `production.py` at implementation time and record findings in the C1 report.
- Templates render uploaded images with width/height + CSS `aspect-ratio` containers copied
  from the existing static-img pattern (no layout shift), `eager` above the fold, `lazy`
  below.
- `README` deploy note: `media/` is runtime data — excluded from source control, backed up
  persistently in any real deployment.

### Documentation duties (implementation phase)

- `docs/imagery-licensing.md`: a new "Admin-managed uploads" section with
  filename · source · licence/consent columns to be maintained by the administrator; the
  honesty rules apply unchanged.
- `docs/data-model.md` §3.4 already lists `profile_image` — add the same row for
  `Speciality.image` and the `WebsiteSectionImage` entity.
- Roadmap & decisions updated in this planning task (see below).

## 4. Decisions & migrations summary

- **ADR-022 (new, appended to `docs/decisions.md`):** Admin-managed website imagery.
  Supersedes ADR-015 (omit `Doctor.profile_image`); keeps ADR-001/002/020 untouched
  (no new frontend dependency; Pillow is a backend validation dependency, not one).
- Models changed: `clinic.Speciality` (+2 fields), `clinic.Doctor` (+2 fields), new
  `website.WebsiteSectionImage` (8 fields). Existing records: all image fields start
  `NULL` → zero visual change after migration; static fallbacks stay in place until admins
  upload, so no data migration and no seed change are required.
- `requirements.txt`: += Pillow (with explicit ADR cross-reference).
- No migrations exist yet — creating or applying them is deliberately **out of scope**.

## 5. Acceptance criteria (for the implementation phase)

1. Administrator can upload, replace, clear and preview images for specialities, doctor
   portraits and every section key, entirely through Django Admin (no code/static edits).
2. Every current image consumer resolves uploaded images with the documented fallback chain;
   removing/clearing an upload returns that surface to today's rendering exactly.
3. Honesty rules preserved: initials fallback for photo-less doctors; no stock photo
   presented as a real doctor's portrait; office/section captions retain "illustrative"
   wording where applicable.
4. Invalid/oversized/Wrong-type uploads rejected with clear admin errors; media cannot
   overwrite source-controlled files.
5. Tests green: upload, replace/clear / missing-image fallback, section-key fallback, RBAC
   (non-admin staff sees nothing; doctors cannot edit speciality images), rendering across
   all inventoried surfaces; full suite stays at 228+ passing with the new migration checks.

## 6. Open decisions (require confirmation)

1. **Keep static demo files?** Recommendation: keep everything under `static/img/` as
   fallbacks and delete nothing; admins opt in per section/speciality/doctor.
2. **Storage backend** for production (local volume vs object storage) — deferred until the
   deployment target (Q5, open in `decisions.md`) is confirmed.
3. **Pillow dependency** — accepted as part of lifting ADR-015? (assumed: yes, since C1 was
   requested).
4. **Dimension policy** hard-block (fail upload) vs warn-only — recommendation: hard block
   for portraits (identity-critical), warn-only for section images.

## 7. Dependencies

- F5 (dashboards) and F6 (final frontend QA) complete **before** implementation starts.
- User approval of this plan (including §6 open decisions) before any code/model work.
- Pillow install into `C:\venvs\anmaya-clinic` at implementation time.
