# Implementation Roadmap — Care_Clinic

**Phase:** 1 — Roadmap (planning only)
Each phase lists objective, tasks, deliverables, dependencies, and completion criteria.

---

## Phase overview

| # | Phase | Status |
|---|---|---|
| 0 | Workspace isolation | ✅ Complete |
| 1 | Requirements & architecture | ✅ Complete |
| 2 | Django foundation | ✅ Complete |
| 3 | Authentication & RBAC | ✅ Complete |
| 4 | Doctor & speciality management | ✅ Complete |
| 5 | Appointment booking | ✅ Complete |
| 6 | Dashboards | ✅ Complete |
| 7 | Frontend implementation | ✅ Complete |
| F | Frontend redesign programme (F1–F6) | 🔄 In progress |
| 7.1 | Hospic-inspired design foundation & homepage | ✅ Complete |
| 7.2 | Animation & transitions (restrained) | ✅ Complete |
| 7.3 | Visual fidelity correction | ✅ Complete |
| 7.4 | UI consistency audit | ✅ Complete |
| 7.4.1 | UI consistency fixes | ✅ Complete |
| 7.4.2 | Public card-system unification | ✅ Complete |
| 8 | Testing & security hardening | ⬜ |
| 9 | Submission preparation | ⬜ |

**Frontend-first sequence (explicit user request):** the remaining frontend phases run
**before** any backend-polishing phase. See the phase notes below.

| # | Phase | Status | Objective |
|---|---|---|---|
| F5 | Dashboards | ✅ | Visual redesign of the four role dashboards (report: `phase-f5-dashboards-frontend-report.md`) |
| F6 | Full frontend QA & approval | ✅ | Whole-app frontend regression, a11y/UX audit, user sign-off (report: `phase-f6-final-frontend-audit-report.md`) |
| C1 | Admin-managed website imagery | ✅ | Upload/replace/preview/manage all website imagery via Django Admin (implementation + user review complete; report: `phase-c1-admin-managed-imagery-report.md`) |
| B0+ | Backend audit & polishing | ⬜ | Backend improvements, incl. findings carried from earlier phases |

> **Frontend programme F1–F6: complete (2026-10-20) — all phases signed off and
> recorded** alongside C1; the frontend work and C1 are committed to
> `origin/main` as `4e0754f` ("feat: complete clinic frontend and
> admin-managed imagery"). B0+ remains pending.

> **C1 plan:** `docs/phase-c1-admin-managed-imagery-plan.md`, implementation report:
> `docs/phase-c1-admin-managed-imagery-report.md`. It reverses ADR-015, adds
> `Speciality.image`, `Doctor.profile_image` and a `website.WebsiteSectionImage` registry,
> requires Pillow, and touches `clinic/models.py`, `clinic/admin.py`, `clinic/migrations/`,
> `website/models.py`, `website/admin.py`, `website/migrations/`,
> `website/templatetags/clinic_images.py`, `config/urls.py` (dev media serving), the
> inventoried templates, and `requirements.txt`.

---

## Phase 2 — Django foundation
**Objective:** A runnable, configurable Django project with the custom user model in place.
**Tasks:**
- Fix `requirements.txt` Django pin to `>=5.2,<5.3` (ADR-010); verify `mysqlclient` builds (ADR-003).
- `pip install -r requirements.txt` into `C:\venvs\anmaya-clinic`.
- Create `config` project with split settings (`base`/`dev`/`prod`), env loading via `python-dotenv`.
- Create `accounts.User`, set `AUTH_USER_MODEL`, first migrations.
- Base templates, Bootstrap 5 static pipeline, root URLs, `django check`.
**Deliverables:** Running dev server, empty home page, migrations applied.
**Dependencies:** Phase 1; MySQL server available.
**Completion criteria:** `python manage.py check` clean; migrations apply on MySQL; login not yet required.

## Phase 3 — Authentication & RBAC
**Objective:** Identity and authorization backbone.
**Tasks:** Login/logout/password reset; patient registration (role locked to PATIENT);
Groups/Permissions sync; role mixins/decorators; scoped querysets (`for_user`); RBAC tests.
**Deliverables:** Working auth + enforced RBAC.
**Dependencies:** Phase 2.
**Completion criteria:** Unauthorized-access tests pass (see Testing strategy).

**Status (implemented):**
- Login/logout/password-reset via `accounts/urls.py`; email-labelled login form
  (`EmailAuthenticationForm`); console email backend in development.
- Patient-only registration (`PatientRegistrationForm`) — `role` forced to PATIENT server-side
  and never read from input; new patients auto-logged-in.
- `sync_roles` management command creates the four role **Groups**, grants a configurable
  permission set, and reconciles membership with each user's `role`.
- RBAC primitives in `accounts/permissions.py`: `role_required` decorator + `RoleRequiredMixin`
  (anonymous → login redirect; wrong role → 403; superuser/admin always allowed).
- 36 tests green (model, form, registration, auth flows, RBAC primitives, sync command).
- **Deferred:** concrete `for_user` scoped querysets live on the domain models they protect
  (`Appointment.objects.for_user`, `clinic` selectors) and are implemented in Phases 4–5; the
  contract is documented in `accounts/permissions.py`.

## Phase 4 — Doctor & speciality management
**Objective:** Catalog and scheduling configuration.
**Tasks:** `Speciality`, `Doctor`, `AvailabilityRule`, `DoctorLeave` models + admin/CRUD UI;
public listing/detail pages; availability rules UI for doctors.
**Deliverables:** Managed catalog with public pages.
**Dependencies:** Phase 3.
**Completion criteria:** Admin can CRUD; public pages render; leave blocks slots.

**Status (implemented):**
- New `clinic` app: `Speciality`, `Doctor` (OneToOne to a DOCTOR-role user), `AvailabilityRule`,
  `DoctorLeave`, with `CheckConstraint`/`UniqueConstraint` integrity and `full_clean()` on save.
- New `website` app: public home, speciality list/detail, doctor list (filter by speciality)
  and doctor detail. Only **active specialities** and **accepting doctors** are shown
  (`Doctor.objects.public()`); inactive/non-accepting/unknown → 404.
- Doctor self-service for availability & leave, with **ownership enforced server-side**
  (scoped querysets → 404 for other doctors' rows; submitted doctor id ignored).
- Admin: `Speciality`/`Doctor` restricted to the Administrator role; `AvailabilityRule`/
  `DoctorLeave` scoped to the logged-in doctor (queryset + object permissions + forced owner).
- `seed_clinic` command creates 5 specialities and 3 doctors (idempotent, synthetic data).
- `sync_roles` extended to grant clinic permissions to the four role groups.
- 94 tests green total (36 Phase 2/3 + 58 new) under both `manage.py test` and `pytest`.
- **DB note:** migrations/tests ran on the documented **SQLite fallback**; MySQL validation
  remains blocked per ADR-003.
- **Deferred to Phase 5:** "leave blocks slots" is enforced when concrete slots are
  materialized/booked (no slot materialization exists yet).


## Phase 5 — Appointment booking (core)
**Objective:** Race-safe booking end to end.
**Tasks:** Slot materialization; `book_slot`/`cancel`/`reschedule` services with locking +
constraints; status state machine; booking UI; reference generation; concurrency tests.
**Deliverables:** Working, safe booking flow.
**Dependencies:** Phase 4.
**Completion criteria:** Booking integrity test suite passes, including a concurrency test.

**Status (implemented):**
- New `appointments` app: `AppointmentSlot` (materialized, `OPEN`/`BOOKED`/`BLOCKED`) and
  `Appointment` (human-readable `CC-YYYY-000123` reference, date/time snapshots, status).
  One active booking per slot is enforced by a **nullable `OneToOneField`** + release-on-cancel
  (portable DB guarantee — ADR-017), since MySQL cannot enforce the conditional unique index
  proposed in the data model (verified against Django 5.2's `supports_partial_indexes` gate).
- `slot_generation.py` materializes slots from active `AvailabilityRule` windows, honors the
  rule/doctor slot length, skips leave and past intervals, and is idempotent (existing `BOOKED`
  slots are preserved). Exposed via `python manage.py generate_slots` (rolling horizon).
- `services.py` holds all mutations (`book_slot`, `cancel_appointment`,
  `reschedule_appointment`, `transition_status`) as `@transaction.atomic` operations using
  `select_for_update()`; RBAC predicates (`can_book_for`, `can_cancel`, `can_reschedule`,
  `can_update_status`) are the single source of truth and are re-checked inside the services.
- Ownership scoping via `Appointment.objects.for_user` (patients self, doctors own schedule,
  receptionist/admin all) so foreign references yield **404** (IDOR prevention). The actor's
  role is read from the session, never from submitted ids.
- Booking/`list`/`detail`/`cancel`/`reschedule` pages (`appointments:*`), status-badge styling,
  nav link, and a "Book appointment" CTA on doctor detail pages.
- `sync_roles` extended with appointment permissions; `generate_slots` added.
- **159 tests pass** under both `manage.py test` and `pytest` (65 appointments tests). The
  MySQL-only concurrency test (`BookingConcurrencyTests`) is **skipped on SQLite** and is
  documented in `docs/mysql-validation.md`.
- **DB note:** migrations/tests ran on the documented **SQLite fallback**; MySQL/InnoDB
  validation and the row-lock concurrency test remain **blocked** per ADR-003.

## Phase 6 — Dashboards
**Objective:** Four role-specific dashboards.
**Tasks:** Patient/Doctor/Receptionist/Admin dashboards; check-in; book-on-behalf;
status actions; availability/leave management.
**Deliverables:** All four dashboards functional.
**Dependencies:** Phase 5.
**Completion criteria:** Role flows verified by tests and manual checks.

**Status (implemented):**
- New `dashboards` app (no models — **no migrations**; ADR-019). A single landing
  route (`/dashboard/`) maps an authenticated user to their role's dashboard and
  redirects; anonymous users go to login and an unrecognised role renders a safe
  "no dashboard" page. The role is always read from the session user.
- **Patient** (`/dashboard/patient/`): own upcoming + past appointments (scoped via
  `Appointment.objects.for_user`), status badges, and a link to book.
- **Doctor** (`/dashboard/doctor/`): own schedule split into today / upcoming / past,
  with permitted status actions (`Confirm`, `Check in`, `Complete`, `No show`) applied
  through `services.transition_status`; a doctor without a profile renders safely.
- **Receptionist** (`/dashboard/receptionist/`): clinic-wide, filterable appointment
  list plus **book-on-behalf** (`/dashboard/receptionist/book/`) that reuses
  `services.book_slot` with validated `ModelChoiceField`s for patient and doctor.
- **Admin** (`/dashboard/admin/`): aggregated statistics (total/today/upcoming/
  completed/cancelled appointments, patients, doctors) and a per-status breakdown,
  derived with `aggregate()`/`values().annotate()` (no N+1).
- **Shared search/filter/pagination** (`dashboards/selectors.py`): optional scope
  (upcoming/today/past/all), date, status, doctor, patient and reference filters are
  applied to an *already ownership-scoped* queryset; malformed input degrades to "no
  filter" instead of erroring, and `Paginator.get_page` makes invalid page numbers
  safe. Filters are preserved in pagination links.
- **Security:** every route is `RoleRequiredMixin`-gated; records resolve through the
  scoped querysets so foreign references return **404** (IDOR prevention); status
  changes are POST-only with CSRF and delegate to `appointments.services`.
- **205 tests pass** under both `manage.py test` and `pytest` (46 new dashboard tests;
  the MySQL-only concurrency test is still skipped on SQLite).
- **DB note:** migrations/tests ran on the documented **SQLite fallback**; MySQL/InnoDB
  validation remains **blocked** per ADR-003.

## Phase 7 — Frontend implementation
**Objective:** Original, accessible UI (design direction in `architecture.md` §8).
**Tasks:** Load and follow the `frontend-design` skill; build public pages and dashboards;
responsive layout; accessibility pass.
**Deliverables:** Polished UI.
**Dependencies:** Phase 6.
**Completion criteria:** Mobile-responsive; keyboard accessible; no copied branding/assets.

**Status (implemented):**
- **Design direction — "calm clinical clarity".** A custom design-system stylesheet
  (`static/css/styles.css`) with design tokens (colour, type, spacing, radii, shadows,
  focus, breakpoints), replacing the previous ad-hoc styles. Brand anchored on the existing
  deep navy + teal; cool light canvas; a humanist serif (Palatino/Georgia) for display
  headings and a system sans for UI/data. Signature "appointment ticket" motif on the
  appointment detail page. **No new frontend dependency** (no Bootstrap was actually loaded
  before; the UI is hand-built CSS — ADR-020).
- **Shared app shell** (`templates/base.html`): skip link, sticky header with brand,
  role-aware primary navigation with `aria-current` active state, a JS-enhanced collapsible
  mobile menu that degrades to an always-visible list without JS, accessible flash messages
  (`role="status"`/`"alert"`), and a footer.
- **Reusable components / partials:** `partials/_field.html` (label + required marker +
  widget + help + inline errors), `partials/_form_errors.html` (non-field errors), status
  badge (`text + dot`, never colour alone), responsive appointment table (`table-wrap--stack`
  stacks rows into labelled cards on small screens, no JS), filters, and pagination.
- **Public site:** full-bleed hero with a real speciality→doctors quick-find form, a
  genuine 3-step "how booking works" sequence, speciality directory/detail, doctor
  directory (progressive auto-submit filter) and doctor detail (profile + weekly availability).
  Home shows only real, DB-derived counts (`HomeView` gained `speciality_count`/`doctor_count`).
  No invented stats, testimonials, awards, or external assets.
- **Auth + appointment flows:** login, register, password reset (form/done/confirm/complete),
  logged-out, appointment list/detail (ticket)/cancel/reschedule, and booking — all preserve
  the existing forms, field names, CSRF, POST/redirect behaviour and context contracts.
  Field-level and non-field errors are shown inline and announced; readable dates/times;
  monospace references; typed+`inputmode`/`autocomplete` inputs.
- **Dashboards + clinic pages:** patient/doctor/receptionist/receptionist-book/admin/no-dashboard
  and availability/leave lists & forms, redesigned without changing any RBAC rule, scoped
  queryset, filter, or pagination behaviour.
- **Accessibility & responsiveness:** semantic landmarks, heading hierarchy, visible
  `:focus-visible` rings, `prefers-reduced-motion` support, `color-scheme: light`, labelled
  controls, table scroll regions, and layouts verified at 360/390/768/1024/1440 px via CSS
  (no horizontal overflow, stacked tables/nav). JavaScript is optional progressive
  enhancement only (`static/js/app.js`); no console-only dependency, no third-party script.
- **Regression:** all **205 tests pass** under `manage.py test` (skipped=1) and
  `pytest -q` (**204 passed, 1 skipped**); `manage.py check` clean; `makemigrations --check`
  reports **no changes** (Phase 7 added zero migrations). A temporary all-roles page-render
  smoke test confirmed every page returns 200 before being removed.
- **Limitation:** no browser-automation/screenshot tooling is available in this environment,
  so visual verification was done by rendered-HTML inspection + CSS review and suite runs,
  not automated screenshots (manual steps listed in the Phase 7 report).
- **DB note:** everything was verified on the documented **SQLite fallback**; MySQL/InnoDB
  validation remains **blocked** per ADR-003.

## Phase 7.1 — Hospic-inspired design foundation & homepage
**Objective:** Re-build the design foundation and homepage in the approved Hospic-inspired
teal direction (per `docs/frontend-design-specification.md`), without changing behaviour.

**Status (implemented):**
- **Approved palette adopted as tokens.** `static/css/styles.css` `:root` now defines the
  mandatory palette (`--color-primary #0EA5A8`, `--color-primary-dark #0B7C80`,
  `--color-primary-soft #E8F8F8`, `--color-surface #FFFFFF`, `--color-text #1F2937`,
  `--color-text-muted #6B7280`, `--color-border #E5E7EB`) with the legacy `--ink-*`/`--brand-*`
  aliases remapped onto it, so every existing page inherits the new palette with no template
  churn. Type switched to a single system sans for display and body; spacing/radii/shadow
  tokens refreshed.
- **Contrast.** Primary buttons and footer/CTA surfaces use dark teal `#0B7C80`/`#086063`
  (white text ≥ 4.5:1); teal `#0EA5A8` is reserved for accents/hover, never small text on
  white. Muted grey is darkened to `#4B5563` on the light-teal tint bands to keep AA.
  Disabled buttons use the border-grey/`#6B7280` treatment.
- **Shared shell** (`templates/base.html`): light sticky header with a teal brand mark, the
  same role-aware navigation and `aria-current` states, an added prominent **Book appointment**
  CTA (→ `doctor_list`), a collapsible mobile menu (JS-enhanced, no-JS fallback) and a new
  three-column footer using only real routes (Home / Specialities / Doctors; Dashboard /
  My appointments or Log in / Register). Logout remains a CSRF-protected POST. Flash messages
  unchanged (still `role="status"`/`"alert"`).
- **Homepage** (`templates/home.html`): full-bleed teal hero with an SVG pattern treatment and
  a real speciality quick-find panel; an at-a-glance strip showing **only genuine**
  `speciality_count`/`doctor_count` (hidden when empty); an About section with a decorative
  CSS/SVG medical visual and a real 3-step product flow; a specialities ("services") grid from
  the live `Speciality` queryset; a doctors grid from `Doctor.objects.public()` with
  initial-based avatars (no fake portraits); and a closing CTA band. Empty states preserved.
- **No invented content.** No ratings, reviews, patient totals, awards, credentials, addresses,
  hours or testimonials. No "why choose us"/packages/blog/testimonials sections.
- **Contracts preserved:** no URL names, view contexts, form field names, RBAC rules, scoped
  querysets, CSRF, or booking logic changed. **No models, migrations, settings or dependencies
  changed.** `static/js/app.js` unchanged.
- **Regression:** `manage.py check` clean; `makemigrations --check` reports no changes;
  `manage.py test` → **205 tests OK (skipped=1)**; `pytest -q` → **204 passed, 1 skipped**;
  rendered-HTML check confirms `/`, `/doctors/`, `/specialities/` return 200 with the new
  sections present.
- **Limitation:** no browser/screenshot automation is available in this environment, so visual
  verification was by rendered-HTML inspection + CSS review, not automated screenshots.
- **DB note:** verified on the documented **SQLite fallback**; MySQL/InnoDB remains **blocked**
  per ADR-003.

## Phase 7.2 — Animation & transitions (restrained)
**Objective:** Add restrained, accessible motion derived from the Hospic analysis
(`docs/animation-reference-analysis.md`) without changing any behaviour or content.

**Status (implemented):**
- **Motion tokens** added to `:root` (`--motion-fast/base/slow/hero/stagger`,
  `--ease-standard/out/in-out`, `--reveal-distance 16px`, `--hover-lift 3px`) — deliberately far
  calmer than the reference's 120px travel and 1.1 hero zoom.
- **Hero entrance (home):** the decorative background pattern fades and subtly scales
  (`hero-bg`, 620ms ease-out); the badge, heading, lead, actions and the quick-find panel
  stagger up (`hero-rise`). CSS keyframes only, no JS.
- **Primary CTA:** the two homepage primary CTAs gain a `.btn__arrow` that nudges 3px on
  `:hover` **and** `:focus-visible` (keyboard parity); the existing background hover is kept.
- **One-time section reveals:** `.reveal` on the five homepage sections; an
  `IntersectionObserver` in `static/js/app.js` adds `.is-visible` once and then `unobserve()`s
  so it never replays; a 2s safety net reveals anything left hidden in-viewport. All of it is
  scoped to `.js`, so with JavaScript off every section stays visible.
- **Cards:** the speciality/doctor hover lift was kept and token-aligned, and extended to
  `:focus-within` for keyboard users.
- **Form focus:** input/select/textarea border + ring transition token-aligned (150ms) — it
  already existed and was only refined.
- **Mobile nav open/close:** the existing `.is-open` toggle now animates open (`nav-open`) and
  close (`nav-close`, cleaned up on `animationend` in `app.js`); the no-JS always-visible
  fallback and `aria-expanded`/Escape/focus-return behaviour are unchanged.
- **Reduced motion:** the global `prefers-reduced-motion: reduce` block now also forces
  `.reveal` to its final state and drops the hero/nav/arrow animations; `app.js` reveals
  everything immediately and skips the observer.
- **No new dependencies, no infinite/ambient animation, no animated statistics, no sticky
  stacked cards, no invented content.** No URL, form field, RBAC, or booking logic changed.
- **Regression:** `manage.py check` clean; `makemigrations --check` reports no changes;
  `manage.py test` → **205 OK (skipped=1)**; `pytest -q` → **204 passed, 1 skipped**; rendered
  `/` returns 200 with 5 `.reveal` sections and 2 arrow CTAs; `git diff --check` clean.
- **Limitation:** visual behaviour was verified by rendered-HTML inspection + CSS review and
  the suite runs (no headless browser available in the project environment), not automated
  screenshots.
- **DB note:** verified on the documented **SQLite fallback**; MySQL/InnoDB remains **blocked**
  per ADR-003.

## Phase 7.3 — Visual fidelity correction
**Objective:** Move the homepage closer to the Hospic reference's visual language
(immersive hero, pill CTAs, larger type, calmer card language, more generous section
rhythm, hero-integrated header) without changing any behaviour, content, or data.

**Baseline:** the Phase 7.3 Visual Fidelity Report (measured local vs. Hospic geometry via
headless Chrome).

**Status (implemented):**
- **Hero is now immersive.** `.hero` is a flex track with `min-height: clamp(620px, 84vh,
  840px)` (**measured 756px @1440**, inside the 750–850 target; natural height on mobile).
  The flat gradient was replaced with layered radial glows + the existing decorative
  pattern (opacity lowered to 0.4). **No photograph is used** — no licensed medical image
  exists in the repo and the brief forbids unlicensed/copyrighted assets, so the refined
  teal gradient + existing pattern is used (per the brief's fallback).
- **Hero H1 at ~80px** via a new `--text-display` clamp (**measured 80px, line-height 84px
  ≈ 1.05, letter-spacing −1.6px = −0.02em**). Lead copy uses `--text-lead` and a tighter
  measure.
- **Pill CTA buttons.** All buttons are now `border-radius: 999px`; the two homepage
  primary CTAs gained a circular `.btn__disc` (an SVG arrow) and render at **exactly 50px**
  (`--lg`); base buttons 46px, `--sm` 34px, table row-actions pinned to 32px so dense
  dashboards are unaffected. The Phase 7.2 arrow nudge on `:hover`/`:focus-visible` is
  preserved and the disc was added to the same treatment (no duplicated logic).
- **Type scale tokens** added to `:root` (`--text-display/h2/h3/lead/body/small/caption`,
  `--leading-*`, `--tracking-*`) and referenced by headings, `.section-title`,
  `.section-intro`, eyebrows and card titles. No web fonts / no new dependencies.
- **Cards** reduced to a **12px radius** with a soft resting elevation token
  (`--shadow-card`) that deepens on hover (`--shadow-card-hover`); spacing/typography
  loosened. The **doctor grid is now 3 columns on desktop** (min track 320px →
  **measured 3 columns @1440**, single column on mobile).
- **Section rhythm** increased: `.band` padding `clamp(3.75rem, 7vw, 6.5rem)` (was
  2.75–4.75rem); section titles/intros enlarged and measure tightened.
- **Hero-integrated header.** `base.html` gained a `{% block header_class %}`; the homepage
  sets `site-header--hero`, which is a **transparent, absolute overlay on desktop**
  (`min-width: 901px`) with inverted brand/nav/CTA colours. **Below 901px the header stays
  sticky and opaque**, so the mobile menu, Escape handling, focus return and
  `aria-expanded` behaviour are untouched. Sticky behaviour is preserved on every other
  page (and on the homepage at mobile widths).
- **Content & contracts unchanged.** No invented data; homepage still renders only
  `specialities`/`doctors`/real counts. No URL names, view contexts, form field names,
  RBAC rules, CSRF, booking logic, models, migrations, settings or dependencies changed.
- **Regression:** `manage.py check` clean; `makemigrations --check` reports no changes;
  `manage.py test` → **205 OK (skipped=1)**; `pytest -q` → **204 passed, 1 skipped**;
  `git diff --check` clean (CRLF notices only); CSS braces balanced (389/389).
- **Visual verification:** headless Chrome (temp `playwright-core` + system Chrome, not
  added to the project) confirmed measured geometry at 1440/390 — hero 756px, H1 80px,
  CTA 50px pills with disc, cards 12px, doctor grid 3-col, transparent header on desktop /
  sticky on mobile, and **no horizontal overflow** on `/`, `/doctors/`, `/specialities/`,
  `/accounts/login/`, `/accounts/register/`. Desktop + mobile screenshots were captured
  but this model cannot render images, so verification is by computed geometry/styles, not
  perceptual review.
- **Limitation:** perceptual screenshot review not possible in this environment (no image
  input); MySQL/InnoDB validation remains **blocked** per ADR-003.

## Phase 7.4 — Application-wide UI consistency audit
**Objective:** Audit the whole app (public, dashboards, auth) for visual/UX drift against the
Phase 7.3 homepage design system.
**Deliverable:** `docs/phase-7.4-ui-audit.md`.
**Status:** ✅ Complete (audit only; no application code changed). 12 findings — 1 high,
5 medium, 6 low — plus documented intentional differences (denser dashboards, homepage-only
transparent header, button size hierarchy).

## Phase 7.4.1 — UI consistency fixes
**Objective:** Implement the 8 targeted, low-risk fixes from the audit.

**Status (implemented):**
- **Radii:** form controls (`input/select/textarea`, hero select) moved from `--radius-sm`
  (8px) to `--radius` (12px), matching the spec's 10–14px band.
- **Field rendering:** `partials/_field.html` adopted for the `reason` field (appointment
  book/cancel, receptionist book); the receptionist reason field now renders help **and**
  errors.
- **Validation UX:** `novalidate` applied consistently to the appointment/receptionist POST
  forms (matching the auth/clinic forms); `partials/_form_errors.html` added; the receptionist
  booking slot errors now render inline.
- **Heading measure:** new `--measure-heading: 64ch` shared by `.page-head`,
  `.section-header` and `.band__head`.
- **Empty states:** new `partials/_empty.html` (explicit heading `level`, optional mark/action);
  all full empty states converted; inline variants left heading-free by design.
- **Spacing:** one-off inline margin styles replaced with token utilities
  (`.mb-0/.mb-3/.mb-4/.mb-5/.mt-6`).
- **Auth:** `.auth-links` block-button misuse fixed via a new `.auth-actions` class.
- **Cleanup:** verified-dead CSS removed (`.card--flush/__body/__media/__eyebrow`, `.slot-doc`,
  `.slot-option--unavailable`, `.confirm--neutral`).
- **Deferred (per scope):** card-system unification (done in 7.4.2) and custom error pages
  (Phase 8).
- **Regression:** `manage.py check` clean; no migrations; `manage.py test` → **205 OK
  (skipped=1)**; `pytest` → **204 passed, 1 skipped**.

## Phase 7.4.2 — Public card-system unification
**Objective:** Give the homepage, speciality listing, speciality detail and doctor listing one
shared card language without changing behaviour, content, or data.

**Status (implemented):**
- **Shared partials extracted:** `templates/partials/_speciality_card.html` (`.service-card`)
  and `templates/partials/_doctor_card.html` (`.doctor-card`) are now the single source of card
  markup, reused by `templates/home.html`, `website/speciality_list.html`,
  `website/doctor_list.html` and `website/speciality_detail.html` — no duplicated markup.
- **Speciality cards:** listing pages now use the homepage `.service-card` + `.service-grid`
  (3 columns desktop → 1 column mobile). Names, descriptions and URLs preserved.
- **Doctor cards:** listing pages and speciality detail now use the homepage `.doctor-card` +
  `.doctor-grid` (3 columns desktop → 1 column mobile), with the initial-based avatar (**no
  photos**), name/speciality/qualification, and a "View profile & book" CTA to the existing
  `get_absolute_url`.
- **Consistent language:** both cards share `border-radius: --radius` (12px), `--shadow-card`
  elevation, spacing, typography, and a hover / `:focus-within` lift (`-3px`, brand border,
  deeper shadow). Reduced-motion still neutralises the transitions (verified `1e-06s`).
- **Design tokens preserved:** teal palette, pill buttons and Phase 7.2 animation/reduced-motion
  untouched. No new fonts or dependencies.
- **Cleanup:** now-unused legacy `.card` / `.card__*` and `.grid--cards` CSS removed.
- **Regression:** `manage.py check` clean; no migrations; `manage.py test` → **205 OK
  (skipped=1)**; `pytest` → **204 passed, 1 skipped**; `git diff --check` clean (CRLF notices
  only); CSS braces balanced (378/378); 40/40 templates compile.
- **Visual verification (headless Chrome, 1440 + 390):** homepage / speciality list /
  speciality detail / doctor list all render 3-col grids on desktop and 1-col on mobile with
  **no horizontal overflow**; card radius 12px and matching shadows; hover + keyboard-focus
  lift confirmed; doctor profile links all return 200. Verification is by computed geometry/DOM
  (this model cannot view images).
- **Limitation:** perceptual screenshot review not possible (no image input); MySQL/InnoDB
  validation remains **blocked** per ADR-003.

## Phase 8 — Testing & security hardening
**Objective:** Prove correctness and safety.
**Tasks:** Full test suite; `web-design-guidelines` audit; `django check --deploy`;
`bandit` / `pip-audit`; fix findings.
**Deliverables:** Green suite + audit report.
**Dependencies:** Phase 7.
**Completion criteria:** All tests pass; no high-severity findings outstanding.

## Phase 9 — Submission preparation
**Objective:** Deliverable package.
**Tasks:** README with setup/credentials/tests; seed-data command; `.env.example`; demo
script; repo hygiene; final documentation review.
**Deliverables:** Submission package.
**Dependencies:** Phase 8.
**Completion criteria:** A reviewer can run the project from the README alone.

---

## Testing strategy

**Tooling:** `pytest` + `pytest-django` + `coverage`, run against **MySQL** (ADR-003).

### Layers
1. **Unit:** model constraints, status state machine, validators, reference generation.
2. **Service:** booking/cancel/reschedule logic, locking behavior, integrity errors.
3. **View/permission:** RBAC matrix, IDOR prevention, anonymous access.
4. **Integration:** full booking flow end to end.

### Essential test cases
- Auth: register (patient-only), login, logout, password reset, inactive user blocked.
- RBAC: Patient A cannot access Patient B's appointment (404, DB unchanged); Doctor cannot
  see another doctor's appointments; Receptionist cannot manage users; anonymous → redirect;
  `role=ADMIN` in registration input is ignored.
- Booking: rejects past dates; rejects unavailable/leave slots; conflict rejected;
  **concurrent double-book attempt → exactly one succeeds**; `IntegrityError` handled.
- Cancellation/reschedule: window enforcement; illegal transitions blocked; slot released.
- Validation: malformed dates/times; missing fields; over-long inputs.

### Manual acceptance
Public booking happy path; each dashboard flow; cancellation window UX; mobile/responsive;
keyboard navigation; direct-URL access checks.

## Security checklist (per phase)
- Secrets only via `.env` (git-ignored); no secrets in code or commits.
- `DEBUG=False` + `ALLOWED_HOSTS` in prod; secure cookie/HSTS flags.
- CSRF on all POST forms; ORM-only queries; server-side validation everywhere.
- Least-privilege DB user; password validators; PII minimization (no clinical data).
- `django check --deploy`, `bandit`, `pip-audit` run before submission.

## Definition of done (project)
1. All §acceptance criteria in `requirements.md` satisfied.
2. Test suite green, including the concurrency test.
3. Documentation (`docs/`) matches the implemented behavior.
4. README enables a clean setup by a third party.
