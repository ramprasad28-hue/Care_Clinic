# Care_Clinic — Frontend Design Specification

> **Status:** Planning specification. No production code, template, stylesheet, script,
> model, migration, dependency, or setting is changed by this document. It describes the
> _target_ visual and interaction direction and the contracts any future implementation
> must preserve.

## 0. How to read this document

- **Verified** — observed directly in this repository (file + line references) or in the
  reference sites' rendered HTML, or stated in the analyst report.
- **Assumption** — a reasonable design inference that has **not** been confirmed by
  inspecting Hospic's compiled CSS, fonts, or animation timings. Assumptions are marked
  `[ASSUMPTION]` and must be validated (e.g. with browser DevTools) before being treated
  as fact.
- This specification does **not** quote exact reference hex codes, font family files, or
  animation durations for the reference template, because those were not verified. Where
  a value is proposed it is either (a) drawn from the approved palette, or (b) explicitly
  labelled as an assumption to confirm.

---

## A. Goals and reference hierarchy

### A.1 Goals

1. Give the public-facing booking flow (specialities → doctors → book → manage) a
   credible, calm, healthcare-appropriate visual language.
2. Keep the app **server-rendered Django with a hand-built CSS design system and
   progressive-enhancement JS only** — no frontend framework, no build step, no CDN
   (see `docs/decisions.md` ADR-020). Any redesign must stay within that constraint.
3. Preserve every existing URL name, view context variable, form field name, permission
   rule, ownership check, and appointment transition (see §K). The redesign is a
   re-skinning + layout exercise, **not** a behaviour change.
4. Never present invented trust signals as real: no fabricated ratings, review counts,
   patient totals, doctor counts, credentials, addresses, hours, prices, testimonials,
   or medical claims. Anything not backed by real data is hidden or omitted (§J).

### A.2 Reference hierarchy

- **Primary reference — Hospic** (`https://hospic.framer.website/`, plus the Framer
  marketplace listing `https://www.framer.com/marketplace/templates/hospic/` and the
  analyst report). Hospic is a Framer marketing template for hospitals/clinics. It
  provides the **section ordering, tone, and layout rhythm** we adapt.
- **Secondary reference — Crawl Corp India** (`https://crawlcorpindia.com/`). A corporate
  IT services site used only for **structural/interaction cues** (a stat strip, a client
  marquee, a services grid, a "schedule a meet" CTA) that translate usefully to a clinic
  context. It is **not** a healthcare brand and its colour scheme is _not_ adopted.
- **Mandatory palette — Care_Clinic teal** (§B). This overrides whatever colours either
  reference uses. The reference informs layout, not colour.

### A.3 What we deliberately do NOT copy

- Hospic's specific brand colours, imagery, logo, copy, or proprietary illustrations.
- Hospic's exact typefaces unless separately licensed and confirmed.
- Hospic's CMS collection content (departments/doctors/blog) as literal content — we map
  the _pattern_ onto Care_Clinic's real models (`Speciality`, `Doctor`, `Appointment`).

---

## B. Colour

### B.1 Approved palette (mandatory)

| Token (proposed name)      | Value     | Role |
|----------------------------|-----------|------|
| `--color-primary`          | `#0EA5A8` | Primary healthcare teal — primary buttons, links, active nav, key accents |
| `--color-primary-dark`     | `#0B7C80` | Hover/pressed states, headings on light teal, borders for emphasis |
| `--color-primary-soft`     | `#E8F8F8` | Light teal surfaces: section tints, hero panel background, badge backgrounds |
| `--color-surface`          | `#FFFFFF` | Page/card background |
| `--color-text`             | `#1F2937` | Primary body & heading text |
| `--color-text-muted`       | `#6B7280` | Secondary text, meta, captions |
| `--color-border`           | `#E5E7EB` | Dividers, card borders, table rules, input borders |

### B.2 Required states (must be defined, not just nominal colours)

Because the mandatory palette gives only one teal, the following states must be defined
explicitly so that interaction and disabled states remain legible and accessible.

- **Primary button**
  - Default: background `#0EA5A8`, text `#FFFFFF`.
  - Hover: background `#0B7C80`.
  - Active/pressed: background `#0B7C80` (optionally 1px darker).
  - Focus-visible: `#0B7C80` background plus a 2–3px focus ring in `#0EA5A8` at ~40%
    opacity offset by 2px (ring colour to be finalised against contrast checks).
  - Disabled: background `#E5E7EB`, text `#6B7280`, `cursor: not-allowed`, no shadow.
- **Secondary/outline button**
  - Default: transparent background, border `#0B7C80`, text `#0B7C80`.
  - Hover: background `#E8F8F8`.
  - Focus-visible: focus ring as above.
- **Ghost/text link**
  - Default text `#0B7C80`; hover `#0EA5A8` with underline; visited state must remain
    distinguishable from unvisited where the browser default would otherwise hide it.
- **Surfaces**
  - Page background: `#FFFFFF` with alternating sections optionally `#E8F8F8`.
  - Cards: `#FFFFFF`, border `#E5E7EB`, subtle shadow token (see §C).
- **Feedback colours** (success/warning/error) — not in the mandatory palette; propose
  accessible defaults and treat as `[ASSUMPTION]` to confirm: success `#166534` on
  `#DCFCE7`; warning `#92400E` on `#FEF3C7`; error `#991B1B` on `#FEE2E2`. These must
  meet WCAG AA for text and must not rely on colour alone (icon + label already exist in
  the message component — see `templates/base.html:69-83`).

### B.3 Contrast requirements

- Teal `#0EA5A8` on white as **text** is below WCAG AA for normal body text.
  - **Rule:** do **not** use `#0EA5A8` for small text on white. Use `#0B7C80` for
    small/medium text where teal text is required.
  - `#0EA5A8` may be used as a large decorative surface (buttons with white text need a
    contrast check: white on `#0EA5A8` is borderline). **Preferred** primary-button
    background is `#0B7C80` if the white-on-`#0EA5A8` ratio fails AA (to be measured).
- `#1F2937` on `#FFFFFF` and on `#E8F8F8` must meet AA (expected to pass; verify).
- `#6B7280` on white is acceptable only for large text or non-essential meta; verify per
  use. Where it fails, fall back to `#1F2937`.
- **Verification step required at implementation time:** run every final
  foreground/background pair through a contrast checker and record results.

### B.4 Current palette (for reference — being superseded)

The currently shipped stylesheet uses an ink/turquoise scheme, **not** the approved
palette: `--theme-color` meta `#0b1f33` (`templates/base.html:6`), brand teal `#0c6e78`,
canvas `#f3f6f8`, footer muted `#c6d5df` (`templates/base.html:92`). The redesign replaces
these values with §B.1 while keeping the same class structure where practical.

---

## C. Typography, spacing, shape, elevation

### C.1 Type

- **Font stack:** no web fonts are currently loaded and no font files are vendored. The
  current CSS uses a system stack. **Recommendation:** continue with a high-quality
  system stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
  Arial, sans-serif`) to honour the no-build/no-CDN constraint. Any custom font would be
  `[ASSUMPTION]` and require a self-hosted, licensed file.
- **Heading scale (proposed, to confirm):**
  | Level | Size (desktop) | Weight | Line height |
  |-------|----------------|--------|-------------|
  | h1    | 2.5–3rem       | 700    | 1.15        |
  | h2    | 1.75–2rem      | 700    | 1.2         |
  | h3    | 1.25–1.375rem  | 600    | 1.3         |
  | body  | 1rem           | 400    | 1.6         |
  | small | 0.875rem       | 400    | 1.5         |
  Headings use `--color-text`; section eyebrows/labels use `--color-primary-dark`.
- Text colour for body copy: `--color-text`; meta/captions: `--color-text-muted`.

### C.2 Spacing & layout

- **Content max width:** propose `1140–1200px` (`[ASSUMPTION]`, confirm against reference).
- **Section vertical rhythm:** consistent large spacing between homepage sections
  (propose `4–6rem` desktop, `2.5–3.5rem` mobile) — `[ASSUMPTION]`.
- **Grid/gaps:** card grids use `gap: 1.5rem` desktop, `1rem` mobile (`[ASSUMPTION]`).
- Keep the existing `.container` and grid utility approach; a redesign should extend the
  token set rather than introduce a framework.

### C.3 Shape & elevation

- **Corner radius:** propose a shared token (`--radius`) around `10–14px` for cards,
  panels, and inputs, with pill radius for badges (`[ASSUMPTION]`).
- **Shadow:** propose one soft elevation token for cards
  (e.g. `0 1px 2px rgba(16,24,40,.06), 0 1px 3px rgba(16,24,40,.10)`) — `[ASSUMPTION]`.
- **Borders:** `1px solid #E5E7EB` for cards, inputs, table rules.

---

## D. Public navigation

### D.1 Desktop

- **Left:** logo/brand link to `home`. Current brand mark is a letter "C" tile plus the
  wordmark (`templates/base.html:21-24`). Keep brand left.
- **Centre/right links** (verified, current): `Specialities` (`speciality_list`),
  `Doctors` (`doctor_list`); when authenticated: `Dashboard` (`dashboards:landing`),
  `My appointments` (`appointments:list`), doctor-only `Availability`/`My leave`, staff
  `Django admin`.
- **Prominent appointment CTA:** the Hospic pattern places a booking CTA in the nav. The
  real destination is the doctor directory (`doctor_list`) — the closest existing entry
  point to booking, since slots are per-doctor. Propose a right-aligned
  `Book appointment` button → `{% url 'doctor_list' %}`. For anonymous users, keep the
  existing `Log in` / `Register` account cluster.
- **Speciality dropdown:** Hospic uses a services/departments dropdown. Propose a
  `Specialities` dropdown listing `Speciality.objects.active()` (same source as
  `HomeView.specialities`) linking to each `speciality.get_absolute_url`. Must be
  **keyboard operable** (see §I). This is a new interaction; treat as `[ASSUMPTION]` that
  it is desired and confirm.

### D.2 Mobile

- Preserve the existing toggle pattern: `button.nav-toggle` with
  `aria-expanded`/`aria-controls`, toggled by `static/js/app.js`. The menu is usable
  **without JS** (progressive enhancement) — the redesign must keep this property.
- Collapse the specialities dropdown into an expandable group.
- Keep the booking CTA visible (either in the bar or at the top of the opened menu).

### D.3 Auth-aware states (verified behaviour to preserve)

- Nav link set is role-aware via `user.is_authenticated`, `user.is_doctor`,
  `user.is_staff` (`templates/base.html:35-45`).
- Active link uses `aria-current="page"` based on `request.resolver_match.view_name`.
- Logout is a **POST form** with CSRF (`templates/base.html:54-57`) — do not replace with
  a GET link.

---

## E. Homepage section plan (Hospic order → Care_Clinic reality)

Below, each Hospic section is mapped to what Care_Clinic can honestly render given its
**actual** models and pages. "Real destination" means an existing URL name.

1. **Hero** — Hospic: big headline, subcopy, two CTAs, hero artwork/panel.
   - Care_Clinic: keep the existing two-column hero (`templates/home.html:6-37`):
     headline + lead + `Book an appointment` (→ `doctor_list`) and `Find a doctor`
     (→ `#doctors`), plus the "Book by speciality" panel form (GET → `doctor_list` with
     `speciality` param). Visual restyle with teal + soft teal panel.
   - **Imagery:** see §G. No verified photo assets exist; use a restrained
     illustration/pattern/abstract panel rather than an unlicensed stock photo.
2. **Trust / rating strip** — Hospic shows `4.9/5`, `2k clients`, `500+ reviews`.
   - **Care_Clinic: OMIT any rating/review/count.** We have no rating or review model.
     **Substitute** with a genuine, data-backed strip: `speciality_count` and
     `doctor_count` (already provided by `HomeView`, both optional/guarded in the
     template). If counts are zero/absent, render nothing (no fake numbers).
3. **Doctor appointment cards** — Hospic: cards inviting a booking.
   - Care_Clinic: the homepage `Doctors` section (`templates/home.html:85-111`) already
     renders real doctors (`doctors`, `doctor.get_absolute_url`) with speciality +
     qualification. Restyle as cards; each links to the doctor profile → booking.
   - Do **not** show per-doctor "next available" unless computed from real slots
     (`appointments.selectors.available_dates` exists and could back it — treat as an
     optional enhancement, `[ASSUMPTION]`).
4. **About + genuine stats** — Hospic: about paragraph + animated counters.
   - Care_Clinic: there is **no `about` page and no stats model**. Options:
     (a) a short, honest About block that is **static text about the product** (not
     invented clinic history), or (b) omit. **Counters: only render for real counts**
     (`speciality_count`, `doctor_count`). Never invent years/patients/satisfaction.
5. **Medical services** — Hospic: services grid (Emergency care, General medicine, …).
   - Care_Clinic: map to **Specialities** (the real `Speciality` model). There is no
     "services" model distinct from specialities. Render from
     `HomeView.specialities` (active, up to 6) — already the case
     (`templates/home.html:61-83`).
6. **Why choose us** — Hospic: 4 feature cards (experienced specialists, advanced
   technology, trusted healthcare, 24/7 emergency).
   - **Care_Clinic: mostly OMIT.** We cannot verify "advanced technology", "24/7
     emergency", or trust claims. If a "why" band is desired it must use only
     **verifiable product facts** (e.g. "See real availability", "Book, reschedule, cancel
     in one place", "Role-based access", "Synthetic demo data") derived from the product,
     not medical/clinical claims. Recommend a small product-benefits band, clearly worded
     as product capabilities. `[ASSUMPTION]` on wording.
7. **Specialities / departments** — Hospic: departments grid.
   - Care_Clinic: `Specialities` section (real model, `speciality.get_absolute_url`) —
     same as item 5; consolidate rather than duplicate (avoid two identical grids on one
     page).
8. **Appointment CTA / form** — Hospic: a booking band with CTA.
   - Care_Clinic: render a CTA band → `doctor_list` (or `appointments:book` requires a
     doctor slug, so it cannot be a generic destination). For anonymous users the CTA
     should route to `doctor_list`; for logged-in patients the same is fine. Do not embed
     a fake booking form on the homepage; the real booking form is doctor-scoped.
9. **Packages / pricing** — Hospic: pricing/packages cards.
   - **Care_Clinic: OMIT as a public "packages" page.** There is no package model. The
     only real price is `Doctor.consultation_fee`, already shown on the doctor profile
     (`doctor_detail.html:38`). Do not fabricate a packages section. (A transparent
     "consultation fee" note on doctor cards is allowed since it is real data.)
10. **Video / testimonials** — Hospic: video testimonials.
    - **Care_Clinic: OMIT.** No testimonial model, no authorized media, and inventing
      patient quotes is prohibited (§J).
11. **Doctors** — Hospic: doctor grid.
    - Care_Clinic: same as item 3. Keep one doctors grid.
12. **FAQ** — Hospic: accordion FAQ.
    - Care_Clinic: there is no FAQ model or page. Either (a) omit, or (b) add a small,
      honest, product-only FAQ (e.g. "How do I cancel?", "Who can book for a patient?" —
      answers describing real app behaviour). If added, it must be an accessible
      disclosure widget (§H/I). Treat as `[ASSUMPTION]` and only with approved copy.
13. **Blog / news** — Hospic: blog collection.
    - **Care_Clinic: OMIT.** No blog model, no posts, no authoring flow.
14. **Closing CTA** — Hospic: final conversion band.
    - Care_Clinic: a closing band with `Book an appointment` → `doctor_list` and,
      for anonymous users, `Register`/`Log in`. Honest, product-only copy.
15. **Footer** — Hospic: multi-column footer.
    - Care_Clinic: current footer is minimal (brand + Specialities/Doctors links,
      `templates/base.html:88-101`). A redesigned footer may add only real destinations:
      `home`, `speciality_list`, `doctor_list`, `accounts:login`,
      `accounts:register`, and (if present) privacy/terms only if such pages exist —
      **they currently do not**, so do not fabricate legal page links. Do **not** invent
      an address, phone number, email, opening hours, or social accounts.

### E.1 Summary table

| # | Hospic section | Care_Clinic treatment | Real data source / destination |
|---|----------------|-----------------------|--------------------------------|
| 1 | Hero | Restyle existing hero | `doctor_list`, home anchor |
| 2 | Rating/trust strip | **Replace** with real counts only | `speciality_count`, `doctor_count` |
| 3 | Doctor cards | Restyle existing doctors grid | `doctors` → `doctor.get_absolute_url` |
| 4 | About + stats | Honest product blurb; real counters only | `speciality_count`, `doctor_count` |
| 5 | Services | Map to Specialities | `specialities` |
| 6 | Why choose us | **Mostly omit** / product facts only | product capabilities |
| 7 | Departments | Merge with Specialities (no duplicate grid) | `specialities` |
| 8 | Booking CTA band | CTA only, no fake form | `doctor_list` |
| 9 | Packages | **Omit** | — |
| 10 | Video/testimonials | **Omit** | — |
| 11 | Doctors | Merge with #3 | `doctors` |
| 12 | FAQ | Omit, or product-only accessible accordion | approved copy |
| 13 | Blog/news | **Omit** | — |
| 14 | Closing CTA | Restyle band | `doctor_list`, `accounts:register` |
| 15 | Footer | Expand with real links only | existing URL names |

---

## F. Existing application pages (must all be restyled consistently)

These pages exist today and must keep their behaviour; the redesign restyles them.

### F.1 Website (`website` app)

- `speciality_list` — grid of speciality cards (`speciality.get_absolute_url`). Context:
  `specialities`.
- `speciality_detail` — breadcrumb + speciality header + doctors grid. Context:
  `speciality`, `doctors`.
- `doctor_list` — filter bar (GET `speciality`, `data-autosubmit`) + doctor cards.
  Context: `doctors`, `specialities`, `selected_speciality`.
- `doctor_detail` — two-column: profile (bio, qualification, registration no.,
  consultation fee, book button) + weekly availability table (only `rule.is_active`).
  Context: `doctor`.

### F.2 Accounts (`accounts` app)

- `login` (`accounts:login`) — auth panel + form + links to register / reset.
- `register` (`accounts:register`) — "patients only" note (test-asserted, see §K) + form.
- `logged_out`, `password_reset_form`, `password_reset_done`,
  `password_reset_confirm` (validlink branch + invalid branch),
  `password_reset_complete`.
- All accounts pages use `container--form` + `auth-panel` and the shared
  `partials/_field.html` / `_form_errors.html`.

### F.3 Appointments (`appointments` app)

- `appointments:list` (`appointments/list.html`) — patient's appointments with
  filters/pagination.
- `appointments:book` (`book.html`) — doctor-scoped booking form (slot radio inputs;
  test asserts `value="{slot.pk}"`), `BookingForm` (slot, reason).
- `appointments:detail` (`detail.html`) — appointment summary incl. `reference` (test
  asserts reference appears), status badge, cancel/reschedule actions gated by permission
  predicates.
- `appointments:cancel` (`cancel.html`) — `CancelForm` (reason).
- `appointments:reschedule` (`reschedule.html`) — `RescheduleForm` (slot).
- Shared `appointments/_status_badge.html`.

### F.4 Dashboards (`dashboards` app)

- `dashboards:landing` — routes user to role dashboard; "No dashboard" fallback
  (test-asserted).
- `dashboards:patient`, `dashboards:doctor`, `dashboards:receptionist`,
  `dashboards:receptionist_book`, `dashboards:admin`, `dashboards:appointment_status`.
- Shared partials: `_appointment_table.html` (responsive stacked table with
  `data-label` cells), `_filters.html` (`AppointmentFilterForm`), `_pagination.html`.
- Stats/badges are real (`today_count`, `upcoming_count`, `status_breakdown`,
  `total_patients`, `total_doctors`).

### F.5 Clinic (`clinic` app — doctor self-service)

- `clinic:availability_list` / `add` / `edit` / `delete` — availability rules table
  (Weekday/Start/End/Slot length/Active), `AvailabilityRuleForm`.
- `clinic:leave_list` / `add` / `delete` — leave table (Start/End/Reason),
  `DoctorLeaveForm`.
- Reachable from the doctor nav (`clinic:availability_list`, `clinic:leave_list`,
  `templates/base.html:38-41`).

### F.6 Django admin

- `admin:index` link is shown to staff in the nav; the admin itself is Django's own UI and
  is out of scope for the custom design system.

---

## G. Image & asset requirements

**Verified:** there are currently **no image assets** referenced in templates; brand mark
is a CSS letter tile. **`Doctor.profile_image` does not exist** — doctor photos were
deliberately omitted (ADR-013/014/015). Therefore:

- **Do not fabricate doctor portraits.** No stock "doctor" faces, no AI-generated
  patients, no copyrighted imagery, no hotlinking Hospic's assets.
- **Preferred approach:** CSS/SVG-based illustration — abstract medical motifs, soft teal
  shapes, line icons (drawn locally), and initial-based avatars for doctors (letter tile
  using `user.get_full_name`). This is honest and build-free.
- **If real photography is later approved:** it must be licensed, credited, and stored
  locally under `static/img/` (no CDN — ADR-020). Provide for:
  - Aspect ratios: hero illustration ~`4:3` or `16:10`; card thumbnails ~`1:1` or `4:3`;
    doctor avatar ~`1:1`.
  - `object-fit: cover` with a defined focal point; never stretch.
  - Explicit `width`/`height` (or aspect-ratio box) to prevent layout shift.
  - **Alt text rules:** meaningful alt for content images; empty `alt=""` for purely
    decorative backgrounds; never put text essential to meaning only in an image.
  - Local organisation: `static/img/home/`, `static/img/specialities/`,
    `static/img/doctors/`, etc.
- Any icon set must be self-hosted/token-based (inline SVG or vendored font), not CDN.

---

## H. Interaction & motion

- **Hover/focus:** buttons, links, and cards get a defined hover state (§B.2) and a
  consistent `:focus-visible` ring. Never remove focus outlines.
- **Transitions:** short, subtle (propose `150–200ms ease-out` on colour/transform —
  `[ASSUMPTION]`). Avoid animating layout-affecting properties.
- **FAQ accordion** (if added): native `<details>/<summary>` for zero-JS accessibility, or
  an ARIA-correct button+region with JS fallback. Must work without JS.
- **Mobile menu:** preserve the current no-JS-usable toggle (`static/js/app.js`), keeping
  `aria-expanded` in sync and returning focus sensibly.
- **Counters** (if used): must animate **to real values only**, and must render the final
  number when JS is off or `prefers-reduced-motion` is set (no motion).
- **`prefers-reduced-motion: reduce`:** disable marquees, counters, and non-essential
  transitions. **No infinite/looping marquees announced by default** — the Crawl Corp
  client marquee is a cue only; we do not have client logos.
- **Progressive enhancement (mandatory):** every page must be fully usable with JS
  disabled. JS may only enhance (`app.js` currently handles nav toggle, confirm dialogs,
  filter autosubmit, and error-focus).
- **Avoid** heavy animation, parallax, autoplaying media, or unnecessary JS.

---

## I. Accessibility & responsive

### I.1 Accessibility

- **Keyboard:** all interactive elements reachable and operable by keyboard; speciality
  dropdown and mobile menu included. Visible focus everywhere.
- **Forms:** preserve `partials/_field.html` (label association via `for`/`id`, required
  marker, help text, field errors) and `_form_errors.html` (non-field errors announced
  with `role="alert"`). Keep server-rendered error messages near their fields.
- **Semantics:** one `h1` per page; logical heading order; landmark regions
  (`header`/`nav`/`main`/`footer` already used); `aria-current` for active nav.
- **Skip link:** preserve `Skip to main content` (`templates/base.html:16`).
- **Contrast:** meet WCAG AA per §B.3; never signal status by colour alone (status badge
  keeps a text label — `appointments/_status_badge.html`).
- **Tables:** keep `scope` on headers and the responsive `data-label` stacked pattern for
  appointment/availability tables.
- **Motion:** honour `prefers-reduced-motion`.

### I.2 Responsive breakpoints

Design and test at **390 / 768 / 1024 / 1440 px**. Stacked tables must remain legible on
mobile; the mobile menu must trap nothing and close predictably; hero becomes single
column; card grids collapse to one column at 390.

---

## J. Content rules (non-negotiable)

The design must **never invent** any of the following. Only real, database-backed or
explicitly approved product copy may be shown:

- Ratings, review counts, star scores, patient testimonials.
- Patient totals, "years of experience", "clients served", satisfaction percentages.
- Doctor counts/credentials beyond the real `Doctor` fields (`qualification`,
  `registration_number`, `bio`, `speciality`).
- Addresses, phone numbers, emails, opening hours, emergency availability, medical
  claims, accreditations, certifications, awards.
- Pricing beyond the real `Doctor.consultation_fee` (shown per doctor).
- Any "24/7", "trusted", "award-winning" style claim not backed by data.

**Rule:** where a Hospic section would require invented data, **omit the section** (or
replace it with a genuine product capability). Unsupported sections degrade to nothing
rather than to fake content. Empty states already exist for zero data (e.g.
`templates/home.html:76-82,104-110`) and must be preserved.

---

## K. Django integration contracts (must not be broken)

The redesign is presentation-only. Any implementation must preserve:

### K.1 URL names (do not rename)

- Website (un-namespaced): `home`, `speciality_list`, `speciality_detail`,
  `doctor_list`, `doctor_detail`.
- `accounts:` `login`, `logout`, `register`, `password_reset`, `password_reset_done`,
  `password_reset_confirm`, `password_reset_complete`.
- `appointments:` `list`, `book`, `detail`, `cancel`, `reschedule`.
- `clinic:` `availability_list`, `availability_add`, `availability_edit`,
  `availability_delete`, `leave_list`, `leave_add`, `leave_delete`.
- `dashboards:` `landing`, `patient`, `doctor`, `receptionist`, `receptionist_book`,
  `admin`, `appointment_status`.
- `admin:index`.

### K.2 Context variables (do not rename)

- Home: `specialities`, `doctors`, `speciality_count`, `doctor_count`.
- Speciality list/detail: `specialities` / `speciality`, `doctors`.
- Doctor list/detail: `doctors`, `specialities`, `selected_speciality` / `doctor`.
- Appointments: list/detail/book/reschedule/cancel context as implemented.
- Dashboards: `upcoming`/`history`/`today`/`past`, `filter_form`, `page_obj`,
  `querystring`, `stats`, `total_patients`, `total_doctors`, `status_breakdown`,
  `today_count`, `upcoming_count`, `show_actions`, `doctor`, `patients`, `doctors`,
  `selected_patient`, `selected_doctor`.

### K.3 Form field names (do not rename)

- `BookingForm`: `slot`, `reason`. `RescheduleForm`: `slot`. `CancelForm`: `reason`.
- `AppointmentFilterForm`: `scope`, `date`, `status`, `doctor`, `patient`, `reference`.
- `ReceptionBookingForm`: `patient`, `doctor`, (slot/…).
- `AvailabilityRuleForm`: `weekday`, `start_time`, `end_time`, `slot_length_minutes`,
  `is_active`.
- `DoctorLeaveForm`: `start_date`, `end_date`, `reason`.
- `PatientRegistrationForm`: `first_name`, `last_name`, `email`, `phone`,
  `password1`, `password2`.
- `EmailAuthenticationForm`: `username` (labelled "Email").

### K.4 Security & behaviour

- **CSRF:** every POST form keeps `{% csrf_token %}` (including logout and all
  filters/actions).
- **Permissions:** role checks (`is_authenticated`, `is_doctor`, `is_staff`) and service
  predicates (`can_book_for`, `can_cancel`, `can_reschedule`, `can_update_status`) must
  gate the UI exactly as today. Do not surface buttons for actions the user cannot take,
  and do not remove server-side enforcement.
- **Queryset scoping:** reads continue through `clinic.selectors`, `appointments.selectors`
  (`available_slots`, `available_dates`, `doctor_on_leave`), `dashboards.selectors`
  (`filter_appointments`, `paginate`), and `Appointment.objects.for_user`.
- **Ownership checks** and appointment **state transitions** stay enforced by
  `appointments.services` (`book_slot`, `cancel_appointment`, `reschedule_appointment`,
  `transition_status`). Templates may hide unavailable actions but must not implement
  logic.
- **No model/migration/settings/dependency changes** for visual work.

### K.5 Template-text contracts asserted by tests (must remain present)

- `accounts`: the register page contains the string **"patients only"**
  (`accounts/tests.py:163`).
- `website`: speciality list/detail include **"Cardiology"** and exclude
  **"Dermatology"**; doctor list shows **"Alice Anderson"** and excludes
  **"Bob Brown"**; doctor detail shows **"Monday"** and **"15 min"**
  (`website/tests.py:49-142`).
- `clinic`: availability page shows **"Monday"** and not **"Tuesday"**; leave page shows
  **"2026-02-01"** and not **"2026-03-01"** (`clinic/tests.py:281-346`).
- `dashboards`: landing shows **"No dashboard"** (`dashboards/tests.py:116`); doctor
  without a profile shows **"no doctor profile"** (`:242`); a link to
  `reverse("doctor_list")` appears (`:204`); a patient's full name appears (`:443`);
  booking renders slot inputs with `value="{slot.pk}"` (`:445`).
- `appointments`: detail shows the appointment **reference** (`:667`); other pages show
  the doctor's full name (`:627`).

Any redesign must keep these strings/behaviours so the existing test suite continues to
pass.

---

## L. Acceptance checklist

**Palette & tokens**
- [ ] All seven approved colours are defined as tokens and used consistently.
- [ ] Hover/focus/active/disabled states defined for buttons and inputs.
- [ ] Every text/background pair passes WCAG AA (results recorded).
- [ ] Teal `#0EA5A8` is not used for small text on white (uses `#0B7C80` instead).

**Structure**
- [ ] Public nav has logo-left + links + prominent booking CTA; mobile menu works
      without JS; auth/role states preserved; logout stays POST.
- [ ] Homepage follows the approved order with only data-backed sections rendered.
- [ ] No invented rating/review/stat/credential/price/address/testimonial content.
- [ ] Every CTA points at a real URL name.
- [ ] Footer links only to real pages.

**Accessibility & responsive**
- [ ] Keyboard-operable nav, dropdown, accordion; visible focus everywhere.
- [ ] One `h1`/page, logical headings, landmarks, skip link, `aria-current`.
- [ ] Forms use the field/error partials; errors announced; labels associated.
- [ ] Status not conveyed by colour alone.
- [ ] Layouts verified at 390/768/1024/1440 px; stacked tables legible.
- [ ] `prefers-reduced-motion` honoured; no default looping marquees.

**Contracts & regression**
- [ ] All URL names unchanged; `reverse(...)` usages still resolve.
- [ ] All context variables and form field names unchanged.
- [ ] CSRF on every POST; permissions and ownership behaviour unchanged.
- [ ] Test-asserted strings still present (§K.5).
- [ ] `python manage.py check` clean; `makemigrations --check` reports no changes.
- [ ] Full test suite passes with no new skips (SQLite) — MySQL still unverified.

---

## Appendix 1 — Verification basis & gaps

- **Inspected in this repo:** `docs/{requirements,architecture,data-model,decisions,
  implementation-roadmap}.md`; `templates/base.html`, `templates/home.html`,
  `templates/partials/*`; `website/templates/website/*`; `accounts/templates/accounts/*`;
  `clinic/templates/clinic/*`; `appointments/templates/**`; `dashboards/templates/**`;
  `static/css/styles.css`; `static/js/app.js`; models/views/forms/urls/selectors/services;
  test assertions listed in §K.5.
- **Reference basis:** `hospic.framer.website` rendered HTML (webfetch);
  `crawlcorpindia.com` rendered HTML (webfetch); the analyst report PDF
  ("Hospic Framer Template Senior Analyst Report", 13 pages).
- **Not verified (must not be asserted):** Hospic's exact hex values, font families/files,
  and animation timings/durations — the analyst report explicitly could not capture these
  and instead recommends a DevTools inspection procedure. All such values here are marked
  `[ASSUMPTION]`.

## Appendix 2 — Known implementation conflicts with the current docs

- `docs/architecture.md` describes doctor self-service under `/dashboard/doctor/...`,
  but the code serves it under `clinic:` (`/clinic/doctor/availability/`, etc.). The spec
  follows the **code**.
- The docs mention `/manage/` for Django admin; the code uses the default `/admin/`.
- Folders named public `/about/`, `/contact/`, `/faq/`, `/packages/`, `/blog/` that Hospic
  features **do not exist** in Care_Clinic; corresponding sections are omitted or
  substituted per §E.

## Appendix 3 — Implementation notes (design foundation & homepage milestone)

Decisions taken while implementing §B–§E that clarify or refine the spec:

- **No speciality dropdown in the header.** The spec's nav dropdown (§D) is **not** built in
  this milestone. It would require `specialities` to be available to every template, and the
  project only configures the `request`/`auth`/`messages` context processors; adding a custom
  processor means editing `settings`, which this milestone forbids. The nav therefore links
  directly to `/specialities/` and `/doctors/`, whose pages already provide filtering. Revisit
  if a navigation context processor is added later.
- **Primary button colour = `#0B7C80`, not `#0EA5A8`.** As anticipated in §B.3: white on
  `#0EA5A8` is ~3:1 (fails AA for small text), so interactive teal surfaces use dark teal
  (`#0B7C80` base, `#086063` hover/active, `darker` for footer) and `#0EA5A8` is reserved for
  accents/decoration/large UI only.
- **Muted text on the light-teal tint** (`.band--tint`) is rendered in `#4B5563` rather than
  `#6B7280`, because `#6B7280` on `#E8F8F8` is ~4.4:1 (just under AA for normal text).
- **Doctor avatars & service icons.** No portrait assets or per-speciality imagery are used:
  doctor cards show an **initial-based avatar** (first letters of the doctor's real name) and
  service cards use a single inline "pulse" icon. This honours the no-fake-identity rule
  (§G) and avoids unlicensed assets.
- **"How it works" is folded into the About section** as a three-step list rather than a
  separate band; the "Why choose us" band is omitted (no non-fabricated proof points exist).
- **Real-count only.** The at-a-glance strip shows `speciality_count`/`doctor_count` from the
  view and renders nothing when those are zero; no other statistics are shown.
- **`static/js/app.js` unchanged.** The existing progressive-enhancement script already drives
  the new markup (`.nav-toggle`, `#site-nav`, `is-open`, autosubmit, confirm, error-focus).
- **README §11** still describes the earlier "calm clinical clarity / navy" direction; it was
  left untouched in this milestone and should be reconciled in a documentation pass.
