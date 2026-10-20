# Phase 7.4 — Application-wide UI consistency audit

**Status:** Audit only. No application code was modified.
**Date:** 2026-10-17
**Scope:** Login, registration, password reset, doctor listing/profile, speciality listing/detail,
appointment booking/list/detail/cancel/reschedule, patient/doctor/receptionist/admin dashboards,
receptionist booking form, plus the shared base template and stylesheet.
**Method:** Static inspection of all 37 templates, `templates/base.html`, `static/css/styles.css`
(1768 lines), and `static/js/app.js`; class-usage cross-checks; inline-style and form-attribute
grep. No perceptual screenshot review (this environment has no image input) — findings are
structural/computed, not pixel-diffed.

---

## 1. Summary

The homepage design system (Phase 7.3) is internally sound, but it was applied **only to the
homepage**. The rest of the application still reads as the earlier Phase 7/7.1 system, so there is
now a visible split between "marketing" pages (homepage) and "everything else".

The most consequential issue is that the **same entities render through two different card
systems**: specialities and doctors use the new `.service-card` / `.doctor-card` on the homepage
but the legacy `.card` (`card__title/text/meta/link`) on the dedicated listing and detail pages.
A visitor moving homepage → list sees the design language change for identical data.

Beyond that, the inconsistencies are mostly **token/spacing hygiene**: form controls are one step
more squared than the documented spec band, four different heading wrappers coexist, `_field.html`
is bypassed in four places (one of which drops validation messages), and eight inline `style=`
attributes hard-code spacing instead of the `--sp-*` scale.

Internal dashboards are **correctly** denser than the homepage and should not be made to copy the
marketing layout. The audit separates those intentional differences from genuine drift.

**Totals:** 1 high, 5 medium, 6 low. No changes to models, migrations, routes, auth, RBAC, forms,
appointment logic or database settings are required or recommended.

---

## 2. Findings

Severity legend: **High** = same data presented two ways / visibly off-system. **Medium** =
behavioural or spec-level drift. **Low** = hygiene, dead code, minor polish.

### 2.1 Cards — same entity, two systems  · **Severity: High**

| Where | Markup | Resting shadow | Radius | Hover | Grid |
|---|---|---|---|---|---|
| Homepage specialities | `.service-card` | `--shadow-card` | 12px | lift + `--shadow-card-hover` | `minmax(300px,1fr)` |
| Homepage doctors | `.doctor-card` | `--shadow-card` | 12px | lift | `minmax(320px,1fr)` |
| `/specialities/` | `.card` + `card__title/text/link` | `--shadow-sm` | 12px | none | `grid--cards` `minmax(260px,1fr)` |
| `/doctors/` | `.card` + `card__title/meta` | `--shadow-sm` | 12px | none | `grid--cards` |
| speciality detail (doctors) | `.card` + `card__title/meta` | `--shadow-sm` | 12px | none | `grid--cards` |

A speciality or doctor is rendered with an icon/avatar, looser spacing and a lift on the homepage,
and as a flat text card on its own listing page. Grid density also changes (3-col vs 4-col).

- **Recommend:** adopt the homepage card components (or a shared `partials/_card_*.html`) on the
  listing pages, allowing a denser variant if width requires it. Keep one card component per
  entity.
- **Files:** `website/templates/website/speciality_list.html`, `doctor_list.html`,
  `speciality_detail.html`; `static/css/styles.css`.

### 2.2 Form-control corner radius below spec band  · **Severity: Medium**

`input/select/textarea` use `--radius-sm` (**8px**), but the design spec §"Corner radius" proposes a
shared token **10–14px for cards, panels and inputs**, and `:root` documents `--radius` (12px) as
"cards, panels, inputs". Inputs therefore render visibly more squared than the cards and panels
around them (`.hero__panel select` inherits the same 8px).

- **Recommend:** point form controls at a `10–12px` radius (e.g. `--radius` or a new
  `--radius-input: 10px`). Buttons are already pills, which is correct and deliberate.
- **Files:** `static/css/styles.css` (the shared input rule; `.hero__panel select`).

### 2.3 Reusable `_field.html` bypassed; one form drops validation output  · **Severity: Medium**

`templates/partials/_field.html` is the canonical field renderer (label + required marker + widget
+ help + errors). Four templates hand-roll the same markup for `reason`:

- `appointments/appointment_book.html:60`
- `appointments/appointment_cancel.html:17`
- `appointments/appointment_reschedule.html` (via slot fieldset only; reason reused)
- `dashboards/receptionist_book.html:97` — **renders the label + widget but neither
  `field__help` nor `field__error`**, so a server-side reason error on the receptionist form is
  not shown at all. This is a genuine functional/validation-consistency defect.

- **Recommend:** replace hand-rolled fields with
  `{% include "partials/_field.html" with field=form.reason %}` (and a slot variant if the custom
  radio layout must stay).
- **Files:** the four templates above.

### 2.4 Inconsistent validation strategy (`novalidate`)  · **Severity: Medium**

Accounts and clinic forms use `novalidate` (server-rendered errors via `_form_errors.html` /
`_field.html`). The appointment forms **omit** it:

- `appointment_book.html:43`, `appointment_cancel.html:15`, `appointment_reschedule.html:42`,
  `receptionist_book.html:77` — no `novalidate`.

Result: auth/scheduling forms show the app's own error styling, while booking/cancel/reschedule
show the browser's native bubbles — two different validation experiences in the same product.

- **Recommend:** adopt one strategy consistently (the existing `novalidate` + `_field.html`
  pattern is the established convention).
- **Files:** the four appointment/receptionist templates.

### 2.5 Four heading/intro wrappers with different measures  · **Severity: Medium**

| Wrapper | Max width | Used by |
|---|---|---|
| `.page-head` | 70ch | public list/detail/booking pages |
| `.band__head` | 64ch | homepage sections |
| `.section-header` | 62ch | `receptionist_book.html` |
| `.dashboard__head` | none | all dashboards |

Same purpose (page/section title + lead), four different measures and margins, so vertical rhythm
and line length drift between page types.

- **Recommend:** collapse to two intents — a page-level head and a section-level head — or align the
  measures to a single token. Dashboards may keep their tighter head by intent.
- **Files:** `static/css/styles.css`; `dashboards/templates/dashboards/receptionist_book.html`.

### 2.6 Empty-state heading level inconsistency  · **Severity: Medium**

`.empty` blocks use different heading levels for the same component:

- `<h2>` — `speciality_list.html`, `doctor_list.html`, `appointment_book.html`,
  `appointment_reschedule.html`
- `<h3>` — `speciality_detail.html:34`
- no heading (just `<p>`) — `.empty--inline` variants in dashboards, booking, reschedule, leave,
  availability

Heading level should reflect the document outline (these usually follow an `<h1>`), not the
component. Mixed levels are an accessibility/heading-order inconsistency.

- **Recommend:** extract an `_empty.html` partial accepting a heading level, or standardise on a
  single level for the full empty state and keep the inline variant heading-free by design.
- **Files:** `website/templates/website/speciality_detail.html` and the list/booking templates.

### 2.7 Two resting card elevations  · **Severity: Medium**

`.card`, `.auth-panel`, `.filters`, `.filter-bar`, `.table-wrap`, `.stat-card`, `.notice`, `.confirm`
use `--shadow-sm`; the new `.service-card` / `.doctor-card` use `--shadow-card`. Two content
surfaces sitting next to each other have visibly different depth.

- **Recommend:** use `--shadow-card` for content cards/panels, keep `--shadow-sm` for inset/utility
  surfaces (tables, filter bars) — and document the rule. Or unify all card-like surfaces.
- **Files:** `static/css/styles.css`.

### 2.8 Inline `style=` attributes hard-code spacing  · **Severity: Low**

Eight instances bypass the spacing scale / component rules:

| File:line | Inline style |
|---|---|
| `appointments/appointment_list.html:14` | `margin-bottom:1.5rem` |
| `appointments/appointment_detail.html:22` | `margin:0` |
| `appointments/appointment_detail.html:37` | `margin-top:2rem` |
| `dashboards/patient_dashboard.html:12` | `margin-bottom:1.5rem` |
| `dashboards/doctor_dashboard.html:12` | `margin-bottom:1.5rem` |
| `dashboards/doctor_dashboard.html:19` | `margin-bottom:1.5rem` |
| `dashboards/receptionist_dashboard.html:12` | `margin-bottom:1.5rem` |
| `templates/home.html:31` | `margin-bottom:.75rem` |
| `website/templates/website/doctor_detail.html:17` | `margin-bottom:1rem` |

- **Recommend:** small spacing utilities (e.g. `.cluster + .cluster`, `.mb-*`) or a scoped rule,
  then remove the inline styles.
- **Files:** the nine templates above + `static/css/styles.css`.

### 2.9 `.auth-links` misused for a block button  · **Severity: Low**

`password_reset_done.html`, `password_reset_complete.html` and `logged_out.html` wrap a single
full-width `.btn--block` inside `.auth-links` — a flex row intended for inline links (it also draws
a top border). The button-in-a-link-row looks and renders oddly.

- **Recommend:** place the button outside `.auth-links`, or add an `.auth-actions` block wrapper.
- **Files:** the three templates; `static/css/styles.css`.

### 2.10 Dead / unused CSS classes  · **Severity: Low**

Defined but referenced by no template (looks like abandoned "image-led card" work and unused
variants):

- `.card--flush`, `.card__body`, `.card__media`, `.card__eyebrow`
- `.slot-doc`, `.slot-option--unavailable`, `.confirm--neutral`

- **Recommend:** remove, or wire them into the unified card component (2.1) if the image-led
  treatment is intended.
- **Files:** `static/css/styles.css`.

### 2.11 No custom error pages  · **Severity: Low**

The stylesheet comment advertises "403/404/500" misc pages (`.notice`), but no `404.html`,
`500.html` or `403.html` templates exist. With `DEBUG=False`, Django's plain default pages render
off-system (no header/footer/teal identity).

- **Recommend:** add minimal `.notice`-based error templates. Reasonable to defer to Phase 8
  (security hardening) rather than this pass.
- **Files:** new `templates/404.html`, `templates/500.html`, `templates/403.html`.

### 2.12 Card focus treatment only on homepage cards  · **Severity: Low**

`.service-card` / `.doctor-card` have `:focus-within`; the legacy `.card` does not, so keyboard users
get a lift/focus cue on the homepage but not on `/doctors/` or `/specialities/`. Resolves once
2.1 unifies the cards; otherwise add `:focus-within` to `.card`.
**Files:** `static/css/styles.css`.

### 2.13 Minor copy/CTA variance  · **Severity: Low**

Homepage doctor CTA reads "View profile & book"; listing pages read "View profile". Homepage
speciality CTA is a link-style action; listing pages use `card__link` "View doctors". Cosmetic;
resolves with 2.1.
**Files:** `website/templates/website/*.html`.

---

## 3. Intentional differences (do NOT "fix")

- **Dashboards are denser** (`.dashboard__head`, `.stat-card`, stacked tables, `.btn--sm`,
  row-actions at 32px). This is correct for an internal tool and should not copy the marketing hero
  or `.band` rhythm.
- **Homepage-only transparent header** (`site-header--hero`, desktop ≥901px) vs sticky headers
  elsewhere — deliberate (documented in Phase 7.3); sticky on mobile for the menu.
- **Button size hierarchy** — `.btn--lg` on hero/CTA, `.btn--sm` in header/tables/row-actions,
  default 46px in forms. Deliberate.
- **Homepage-only sections** (`.hero`, `.band`, `.band--tint`, `.cta-band`) — not expected on
  app pages.
- **Unique surfaces** — `.ticket`, `.confirm`, `.auth-panel`, `.notice` — intentional per-purpose
  treatments.
- **Form controls at 8px** is *not* listed as intentional — it conflicts with the documented token
  intent (see 2.2).

## 4. What is already consistent (keep)

- One status badge partial (`_status_badge.html`), text + dot, never colour alone.
- Shared partials: `_appointment_table.html`, `_pagination.html`, `_filters.html`,
  `_form_errors.html`, `_field.html`.
- Breadcrumbs on every detail/booking page.
- Global `:focus-visible` plus explicit focus styles for interactive controls.
- Buttons unified as pills with consistent primary/secondary/danger/ghost variants.
- Page widths: `.container` (1160), `container--form` (520), `.auth-panel` (480) used consistently.
- `main` vertical padding consistent across non-home pages.

---

## 5. Files likely to require modification

| File | Findings |
|---|---|
| `static/css/styles.css` | 2.1, 2.2, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.12 |
| `website/templates/website/speciality_list.html` | 2.1, 2.6, 2.13 |
| `website/templates/website/doctor_list.html` | 2.1, 2.6, 2.13 |
| `website/templates/website/speciality_detail.html` | 2.1, 2.6 |
| `website/templates/website/doctor_detail.html` | 2.8 |
| `appointments/templates/appointments/appointment_book.html` | 2.3, 2.4 |
| `appointments/templates/appointments/appointment_cancel.html` | 2.3, 2.4 |
| `appointments/templates/appointments/appointment_reschedule.html` | 2.4 |
| `appointments/templates/appointments/appointment_list.html` | 2.8 |
| `appointments/templates/appointments/appointment_detail.html` | 2.8 |
| `dashboards/templates/dashboards/receptionist_book.html` | 2.3, 2.4, 2.5 |
| `dashboards/templates/dashboards/receptionist_dashboard.html` | 2.8 |
| `dashboards/templates/dashboards/patient_dashboard.html` | 2.8 |
| `dashboards/templates/dashboards/doctor_dashboard.html` | 2.8 |
| `accounts/templates/accounts/password_reset_done.html` | 2.9 |
| `accounts/templates/accounts/password_reset_complete.html` | 2.9 |
| `accounts/templates/accounts/logged_out.html` | 2.9 |
| `templates/home.html` | 2.8 |
| *(new)* `templates/partials/_empty.html`, `templates/404.html`/`500.html`/`403.html` | 2.6, 2.11 |

**No changes** to: models, migrations, URLs/route names, views, auth, RBAC, forms, booking
services, CSRF, or database settings.

---

## 6. Potential regression risks

- **Card unification (2.1) is the highest-risk change** — it rewrites markup on public-facing list
  pages and must preserve the responsive `grid--cards` behaviour, the empty states, and the
  `aria-current`/focus states. Verify at 1440/768/390 and check for horizontal overflow.
- **Input radius (2.2) is global** — it touches every form, including login/register, booking,
  filters and the hero panel. Low functional risk, wide surface; verify selected/error states.
- **Empty-state heading levels (2.6)** may be asserted by existing tests or affect heading-order
  accessibility; check `manage.py test` and any a11y assertions before merging.
- **`novalidate` additions (2.4)** change client-side validation timing on booking/cancel/
  reschedule; ensure server-side errors still render and the `data-guard` (double-submit) script
  and booking tests are unaffected.
- **Removing dead CSS (2.10)** is safe only if nothing is added later by JS — confirm no
  `classList.add` references those names in `static/js/app.js`.
- **Do not** "prettify" dashboards toward the marketing layout — that would regress usability and
  is explicitly out of scope.
- **Verification limitation:** screenshots cannot be perceptually reviewed here (no image input).
  Confirm with computed geometry / DOM assertions in headless Chrome, as in Phase 7.3.

---

## 7. Proposed implementation order

Ordered by risk (lowest first), so each step is independently verifiable.

1. **Dead CSS + token decisions** (2.7, 2.10) — no visual change; establishes the card/elevation
   rule before anything else moves.
2. **Form-control radius** (2.2) — one global rule; verify all forms.
3. **Heading wrappers + empty-state standardisation** (2.5, 2.6) — CSS + `_empty.html` partial.
4. **Adopt `_field.html`** and fix the receptionist reason errors (2.3).
5. **Unify `novalidate` strategy** (2.4) — align appointment forms with the rest.
6. **Replace inline styles with utilities** (2.8) — mechanical.
7. **`.auth-links` block-button cleanup** (2.9) — three templates.
8. **Card-system unification on listing pages** (2.1, 2.12, 2.13) — largest visible change; do last
   with full responsive verification.
9. **(Phase 8) custom error pages** (2.11) — defer to security-hardening phase.

Steps 1–7 are low-risk, token-level consistency work. Step 8 delivers the largest fidelity gain and
carries the most review weight. Step 9 is deliberately deferred.

---

## 8. Verification / constraints for the implementation pass

- Preserve **all** uncommitted Phase 7/7.1/7.2/7.3 changes; do not reset, revert or stash.
- Keep the approved teal palette, motion tokens and `prefers-reduced-motion` handling intact.
- No new dependencies; no web fonts; no licensed assets.
- Never invent content (counts, ratings, credentials, hours, prices).
- Do not commit or push.
