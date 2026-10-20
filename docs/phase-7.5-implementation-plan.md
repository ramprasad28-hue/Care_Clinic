# Phase 7.5 — Premium Editorial Design Implementation Plan

> **Type:** Planning only. **No application code, template, stylesheet, script, test, setting,
> model, migration, dependency, or configuration was changed to produce this document. Nothing
> was installed, committed, or pushed.**
> **Date:** 2026-10-17
> **Project:** `C:\Users\Ramprasad\OneDrive\Desktop\Care_Clinic`
> **Approved direction:** the hybrid concept from `docs/frontend-design-exploration.md` —
> **Concept A (Editorial Clinical) as the visual identity**, **Concept C (Modern Medical Journal)
> as the layout grammar**, and **exactly one** dimensional hero element inspired by
> **Concept B (Immersive Depth)**, realised with **CSS/SVG pseudo-3D** only.
> **Skills applied:** `frontend-design` (design/quality floor, loaded and followed) and
> `web-design-guidelines` (final audit; rule-set fetched from
> `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`).
> Neither skill authorises changes outside this planning phase.

---

## 0. Scope, authority and non-negotiables

This plan sequences the implementation of the approved hybrid. It is constrained by, and must
not violate, the following (all verified in the repo):

1. **ADR-020** (`docs/decisions.md:201-221`) — hand-built CSS, **no framework, no build step, no
   CDN, no web fonts**, no SPA. A single optional `static/js/app.js` for progressive enhancement.
2. **Server-rendered Django** (`docs/architecture.md`) — templates + CSS + tiny vanilla JS. **No
   React/Next.js.** **No Three.js or GSAP** in this phase (brief).
3. **The behaviour contract** (`docs/frontend-design-specification.md` §K): URL names, context
   variables, form field names, CSRF, RBAC/ownership, service-layer transitions, DB constraints,
   and the **test-asserted strings** must be preserved. This is a re-skin + layout exercise.
4. **Content honesty** (spec §J): never invent ratings, reviews, counts, credentials, addresses,
   hours, prices, testimonials, or medical claims. Unsupported sections degrade to empty states.
5. **Preserve all pre-existing uncommitted work** (the Phase 7.x changeset). No reset/revert/
   discard/stash/clean. Do not commit or push.

**Non-visual work is explicitly out of scope:** no model/migration/settings/route/auth/form/
booking-logic changes.

---

## 1. Baseline inventory (verified)

### 1.1 Templates (~40 files; template-parse 40/40)

| Family | Files |
|---|---|
| Shell | `templates/base.html` (139 lines) |
| Home | `templates/home.html` (173 lines) |
| Shared partials | `templates/partials/_field.html`, `_form_errors.html`, `_empty.html`, `_speciality_card.html`, `_doctor_card.html` |
| Public (website) | `website/templates/website/speciality_list.html`, `speciality_detail.html`, `doctor_list.html`, `doctor_detail.html` |
| Accounts | `accounts/templates/accounts/login.html`, `register.html`, `logged_out.html`, `password_reset_form.html`, `password_reset_done.html`, `password_reset_confirm.html`, `password_reset_complete.html` |
| Appointments | `appointments/templates/appointments/appointment_book.html`, `appointment_cancel.html`, `appointment_reschedule.html`, `appointment_list.html`, `appointment_detail.html`, `_status_badge.html` |
| Clinic (doctor self-service) | `clinic/templates/clinic/availability_list.html`, `availability_form.html`, `availability_confirm_delete.html`, `leave_list.html`, `leave_form.html`, `leave_confirm_delete.html` |
| Dashboards | `dashboards/templates/dashboards/patient_dashboard.html`, `doctor_dashboard.html`, `receptionist_dashboard.html`, `receptionist_book.html`, `admin_dashboard.html`, `no_dashboard.html`, `_appointment_table.html`, `_filters.html`, `_pagination.html` |

### 1.2 CSS components (`static/css/styles.css`, ~1,732 lines; braces 378/378)

- **Tokens** (`:root`, lines 10–131): approved palette + ink/brand scales + surfaces + semantic;
  type scale (`--text-display/h2/h3/lead/body/small/caption`, leading/tracking); spacing
  (`--sp-1..9`); radii (`--radius-sm/-/lg/pill`); shadows (`--shadow-sm/md/lg/card/card-hover`);
  layout (`--container`, `--measure-heading`, `--header-h`, `--hero-min-h`); **motion**
  (`--motion-fast/base/slow/hero/stagger`, `--ease-*`, `--reveal-distance`, `--hover-lift`);
  focus ring.
- **Base/shell**: reset, `html/body`, `.container`, `.container--form`, `.skip-link`,
  `.site-header` (+ `site-header--hero`), `.brand`/`.brand__mark`, `.nav-toggle`, `.site-nav`,
  `.site-user`, `.main--flush`, `.messages`/`.message`, `.site-footer*`.
- **Buttons**: `.btn` + `--primary/--secondary/--ghost/--danger`, `--lg/--sm/--block`,
  `--arrow`, `.btn__disc`, `.btn__arrow`, `.link-button`.
- **Forms**: `.field` + `__label/__help/__error`, `.field--error`, `.filter-bar`, `.filters`,
  `.inline-form`, `.hero__panel select`.
- **Cards**: `.service-card` (+ `__icon/__title/__text/__link`), `.doctor-card`
  (+ `__head/__name/__qual/__meta`), `.avatar`. (Legacy `.card`/`.card__*`/`.grid--cards`
  removed in Phase 7.4.2.)
- **Hero** (lines 545–…): `.hero`, `.hero__grid/copy/lead/actions/panel`, `.hero-badge`;
  layered radial-gradient + SVG pattern (CSS-only "immersive" base).
- **Home bands**: `.band`, `.band--tint`, `.band--compact`, `.band__head/__more`,
  `.section-title`, `.section-intro`, `.eyebrow` (ALL-CAPS tracked label — slated for removal),
  `.trust-strip/item/value/label`, `.about-grid/copy/steps/visual`, `.cta-band`, `.btn--inverse`.
- **Layout helpers**: `.grid`, `.grid--two`, `ul.grid`, `.service-grid`, `.doctor-grid`.
- **Misc/components**: `.pill`/`.pill--neutral`, `.badge`, `.empty`/`.empty--inline`,
  `.breadcrumb`, `.table-wrap`/`--stack`, `.data-table`, `.detail-list`, `.ticket`, `.confirm`,
  `.notice`, `.stat-card`, `.dashboard__head`, `.num`, `.muted`, spacing utilities
  (`.mb-0/.mb-3/.mb-4/.mb-5/.mt-6`), motion `.reveal` + keyframes, global
  `prefers-reduced-motion` block, `:focus-visible` rings.

### 1.3 JavaScript behaviour (`static/js/app.js`, 170 lines; dependency-free IIFE)

Mobile-nav toggle (`aria-expanded`, Escape→close+return focus, close-on-link); filter
auto-submit (`[data-autosubmit]`); confirm dialogs (`form[data-confirm]`); double-submit guard
(`form[data-guard]`); focus-first-error; **one-shot `.reveal`** via `IntersectionObserver`
(`unobserve()` after first reveal, `rootMargin:"0px 0px -10% 0px"`, reduced-motion guard,
2 s safety net). No keyframe-driven JS; no animation library.

### 1.4 Page families

| Family | Entry points | Notes |
|---|---|---|
| Public marketing + discovery | `/` ; `/specialities/` ; `/specialities/<slug>/` ; `/doctors/` ; `/doctors/<slug>/` | Home = editorial identity; listings/detail = journal grammar |
| Auth | `/accounts/login/`, `/register/`, `/logout/` (POST), password reset ×4 | `container--form` + `.auth-panel`; register keeps string **"patients only"** |
| Booking | `/appointments/book/`, `/<ref>/`, `/<ref>/cancel/`, `/<ref>/reschedule/` | slot radios assert `value="{slot.pk}"`; detail asserts the **reference**; `novalidate` + `_field.html` |
| Patient list | `/appointments/` | filters, pagination, status badge |
| Clinic self-service | `/clinic/doctor/availability/…`, `/clinic/doctor/leave/…` | tables, forms, confirm-delete |
| Dashboards | `/dashboard/…` (patient, doctor, receptionist, receptionist/book, admin, no-dashboard) | **intentionally dense**; keep practical |

### 1.5 Current verification baseline (must not regress)

- `python manage.py check` → clean; `makemigrations --check --dry-run` → no changes.
- `python manage.py test` → **205 OK (skipped 1)**; `pytest -q` → **204 passed, 1 skipped**.
- `git diff --check` → clean (CRLF notices only); CSS braces 378/378; templates 40/40 compile.
- Rendered geometry (headless Chrome, Phase 7.4.2): home/listings 3-col desktop, 1-col mobile,
  radius 12px, no horizontal overflow; hover/`:focus-within` lift `-3px`; reduced-motion
  `transition-duration: 1e-06s`.

### 1.6 Environment caveats (affect verification, not the plan)

- **No image input** in this environment → perceptual screenshot review is impossible;
  verification is **computed geometry/DOM + rendered-HTML inspection**, as in Phases 7.3–7.4.2.
- Browser tooling is a **throwaway temp install** (`playwright-core` + system Chrome under
  `…\Temp\opencode\browserqa`); **never** added to the project.
- **Stale-server trap (found in 7.4.2):** a long-running `runserver --noreload` served cached
  templates and made fresh edits look unapplied. Always restart a **fresh** server before visual
  verification.
- **MySQL/InnoDB validation remains blocked** (ADR-003); suite runs on the SQLite fallback.

---

## 2. Target design system (extend, never replace)

The hybrid **extends** the existing token system; it does not introduce a new one.

- **Colour (unchanged values, re-roled):** paper/ink-rich surfaces; hairlines as the primary
  structural device; `#0B7C80` for interactive teal + small text; `#0EA5A8` reserved for large
  decorative surfaces; `#E8F8F8` for occasional full-bleed tint. No small teal text on white.
- **Type (new roles, no downloads):** **display = system serif** stack
  (`ui-serif, "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, "Times New Roman",
  "Liberation Serif", serif`) for H1/H2/section titles and editorial entry titles; **UI/body =
  existing system sans**; **data = existing system mono** for references/slot times only.
- **Cards:** evolve the **shared** `_speciality_card.html` / `_doctor_card.html` into **editorial
  entries** (hairline/rules, serif title, narrow description, underline CTA) — one card system
  per entity, kept shared across home + listing + detail pages (preserves the Phase 7.4.2 fix).
- **Hero:** editorial white/soft hero + **one** dimensional plate (CSS `perspective` +
  `translateZ`), gated by `prefers-reduced-motion`, `pointer: fine`, and a min width.
- **Motion:** reuse `--motion-*`, `--reveal-distance`, `--hover-lift`, `.reveal` and the existing
  observer. Add bounded depth tokens **only if** the hero needs them (`--perspective`,
  `--tilt-max`). **No infinite/ambient animation.**

---

## 3. Phased implementation sequence

Each phase is small, independently verifiable, and reversible. **Every phase must finish with
the §6 regression checklist and the §8 verification method** before the next begins. "Files" lists
the *expected* change set; confirmation happens with `grep`/`git status` at implementation time.

Fixed verification widths for every phase: **390 / 768 / 1024 / 1440 px**.

---

### Phase 0 — Baseline capture & guardrails (no code change)

- **Intended result:** a recorded pre-change baseline so any visual/behavioural regression is
  detectable.
- **Files:** none in-repo. Metrics/screenshots written to the **temp** dir only
  (`…\Temp\opencode\…`), never the project.
- **Reuse/refine/replace/introduce:** none.
- **Accessibility/responsive:** capture the four widths + a keyboard-tab trace + a
  reduced-motion pass of current pages.
- **Regression tests:** `check`, `makemigrations --check`, `manage.py test`, `pytest -q`,
  `git diff --check` — record outputs verbatim.
- **Visual verification:** record geometry for `/`, `/specialities/`, `/doctors/`,
  `/doctors/<slug>/`, `/accounts/login/`, `/appointments/`, `/dashboard/patient/`.
- **Completion criteria:** baseline numbers match §1.5; baseline artefacts stored off-repo.

---

### Phase 1 — Typography foundation (tokens only)  ·  identity spine

- **Intended result:** editorial voice appears — H1/H2/section titles render in a **system
  serif**; UI stays sans; data uses mono. No layout/markup change yet.
- **Files:** `static/css/styles.css` (add `--font-display-serif`, `--font-mono` role, a committed
  display scale/tracking; apply serif to headings/`.section-title`/entry titles; add
  `text-wrap: balance/pretty` on headings and `font-variant-numeric: tabular-nums` for `.num`
  and time/meta cells).
- **Reuse:** type-scale tokens, `--leading-*`, `--tracking-*`. **Refine:** heading font-family +
  tracking. **Replace:** none. **Introduce:** the serif token + a documented fallback chain.
- **Accessibility/responsive:** serif line-height ≥ sans; display measure **< 80ch**; confirm
  serif is legible at 390 px; no FOUT (system font).
- **Regression tests:** `check`, `manage.py test`, `pytest -q` (template-free change → expect no
  failures); confirm no heading-order changes.
- **Visual verification:** compare heading rendering at 390/768/1024/1440; measure H1 width/line
  length; capture per-platform serif resolution where possible.
- **Completion criteria:** serif tokens present and applied; **font-evaluation decision logged**
  (see §5 D1); suite green; no layout shift vs baseline.
- **Note (font evaluation):** record measured availability of `ui-serif`/Georgia/Palatino/Iowan
  on Windows Chrome (available here) and document the fallback behaviour for macOS/iOS/Android/
  Linux by **CSS stack reasoning** (cannot be measured in this environment). If the serif proves
  too variable, fall back to Phase 1b: **single sans with a committed display weight/tracking**
  (Concepts hold; identity rests on spacing + rules instead).

---

### Phase 2 — Section headers & elevation rule (remove the flagged defaults)

- **Intended result:** the ALL-CAPS tracked `.eyebrow` device is gone; section intros become a
  **short teal rule + serif H2** (+ optional sentence-case caption). Heading wrapper measures are
  unified. One resting elevation rule for content surfaces.
- **Files:** `static/css/styles.css`; `templates/home.html`; **every template using `.eyebrow`
  (grep first** — known: `templates/home.html`; verify others); `dashboards/…/receptionist_book.html`
  (`.section-header`).
- **Reuse:** `.section-title`, `.section-intro`, `--measure-heading`. **Refine:**
  `.page-head`/`.band__head`/`.section-header` → one measure. **Replace:** `.eyebrow` styling +
  its template usages. **Introduce:** `.section-rule` (or equivalent) primitive.
- **Accessibility/responsive:** no meaning carried by the removed label; heading order unchanged;
  rule is decorative (`aria-hidden` where standalone).
- **Regression tests:** `manage.py test` (home/website/dashboard tests), `pytest -q`.
- **Visual verification:** all four widths; check section rhythm and measure.
- **Completion criteria:** no `.eyebrow` remains; measures aligned; suite green.

---

### Phase 3 — Shared editorial cards (speciality + doctor)  ·  layout grammar

- **Intended result:** specialities and doctors render as **editorial entries** (rules, serif
  title, narrow description, underline CTA; doctor keeps the initial avatar) on **home,
  `/specialities/`, `/specialities/<slug>/`, `/doctors/`** — still one shared component per entity.
- **Files:** `templates/partials/_speciality_card.html`, `templates/partials/_doctor_card.html`,
  `static/css/styles.css` (grids `.service-grid`/`.doctor-grid` and entry styles). Parent
  templates normally need **no** change (they include the partials); confirm with `git status`.
- **Reuse:** the two partials + grids + `_empty.html`. **Refine:** `.service-card`/`.doctor-card`
  → editorial entries. **Replace:** the SaaS-card visual idea (uniform rounded shadow cards).
  **Introduce:** none (reuse the existing partials).
- **Accessibility/responsive:** entry title remains an `<h3>` under section `<h2>`; anchor carries
  the name; hover **and** `:focus-within` parity; 3-col desktop → 1-col 390; no overflow.
- **Regression tests:** website tests asserting **"Cardiology"** present / **"Dermatology"**
  absent, **"Alice Anderson"** present / **"Bob Brown"** absent, doctor detail shows **"Monday"**
  and **"15 min"**; full `manage.py test` + `pytest -q`.
- **Visual verification:** 390/768/1024/1440 on home + both listings + speciality detail; check
  column counts, link integrity (200), no overflow.
- **Completion criteria:** one card system, editorially styled; all listing/detail tests green.

---

### Phase 4 — Hero composition + the single pseudo-3D element  ·  the one bold moment

- **Intended result:** home hero is the editorial hybrid — headline-led composition with the real
  "Find a doctor" `GET` form restyled as an editorial control, plus **one** floating
  "open times" plate given depth with CSS `perspective`/`translateZ` and a subtle pointer tilt.
- **Files:** `templates/home.html`; `static/css/styles.css`; `static/js/app.js` (small,
  feature-detected tilt module **only if** adopted — see §5 D2). Optionally a new
  `templates/partials/_hero_plate.html` for the decorative plate.
- **Reuse:** `.reveal` + observer, `--motion-hero`, form/field partials, `hero` gradient base.
  **Refine:** `.hero*`. **Replace:** the boxed-panel hero presentation. **Introduce:** the plate
  (decorative; or real-data only if context already provides it — see D2).
- **Accessibility/responsive:** decorative layers `aria-hidden`; white-on-`#0B7C80` contrast
  (≈5.6:1); **plate must not carry essential information**; tilt disabled under reduced-motion,
  coarse pointer, and narrow widths (clean static hero); keyboard unaffected; ≥44 px targets.
- **Regression tests:** home view context unchanged (`specialities`, `doctors`,
  `speciality_count`, `doctor_count`); full suite; confirm the hero form still GETs to
  `doctor_list` with `speciality`.
- **Visual verification:** 390/768/1024/1440; reduced-motion emulation; **no-JS**; touch
  emulation (tilt off); no overflow; transform/opacity only.
- **Completion criteria:** one and only one dimensional element; gated correctly; suite green;
  no new backend dependency.

---

### Phase 5 — Home bands & editorial components

- **Intended result:** About (incl. 3-step list), trust strip, specialities/doctors sections and
  the closing CTA band read as **journal-structured** editorial bands (rules, captions, generous
  whitespace); introduce a **photo-ready figure plate** (decorative placeholder now) where a large
  visual is wanted.
- **Files:** `templates/home.html`; `static/css/styles.css` (bands, `.about-*`, `.trust-*`,
  `.cta-band`, figure-plate, dividers).
- **Reuse:** band rhythm, `.band--tint`, SVG motif approach. **Refine:** `.about-visual`,
  `.trust-strip`, `.cta-band`. **Replace:** duplicated gradient-card decoration. **Introduce:**
  `.figure-plate` (aspect-ratio box; explicit `width`/`height` or `aspect-ratio`).
- **Accessibility/responsive:** figure plate `aria-hidden` + reserved space (low CLS); caption
  shown as text, not baked into an image; contrast on tint bands (`#4B5563` rule retained).
- **Regression tests:** full suite; counts render only when non-zero.
- **Visual verification:** all four widths; no overflow; verify reveal one-shot.
- **Completion criteria:** home reads as one coherent editorial page; suite green.

---

### Phase 6 — Public listing & detail pages alignment

- **Intended result:** `/specialities/`, `/specialities/<slug>/`, `/doctors/`,
  `/doctors/<slug>/` use the editorial page-head grammar, refined filter bar, pill meta,
  `.detail-list`, and the availability table — consistent with home.
- **Files:** `website/templates/website/speciality_list.html`, `speciality_detail.html`,
  `doctor_list.html`, `doctor_detail.html`; `static/css/styles.css`.
- **Reuse:** `_speciality_card`/`_doctor_card` (Phase 3), `_empty.html`, breadcrumbs, tables.
  **Refine:** `.page-head`, `.filter-bar`, `.detail-list`, `.pill`. **Replace:** none.
  **Introduce:** none.
- **Accessibility/responsive:** stacked table (`data-label`) intact; filter `label` clickable;
  `aria-current`; `:focus-visible`; 390 stack → 1440 multi-col.
- **Regression tests:** all website tests (§K.5 strings), full suite.
- **Visual verification:** four widths per page; link checks 200; no overflow.
- **Completion criteria:** listings/detail match the editorial system; tests green.

---

### Phase 7 — Auth pages

- **Intended result:** login/register/logout/reset pages use the editorial system with a calm
  `.auth-panel`, correct input radius, inline errors, and consistent `.auth-actions`.
- **Files:** `accounts/templates/accounts/*.html` (7 files); `static/css/styles.css`.
- **Reuse:** `.auth-panel`, `_field.html`, `_form_errors.html`, `.container--form`.
  **Refine:** auth panel typography/spacing. **Replace:** none.
- **Accessibility/responsive:** labels associated; errors inline + focus-first-error; register
  keeps the exact string **"patients only"**; ≥44 px targets; single column at 390.
- **Regression tests:** accounts tests (incl. the "patients only" assertion), full suite.
- **Visual verification:** all four widths; error state; keyboard.
- **Completion criteria:** auth family consistent; tests green.

---

### Phase 8 — Booking family (book / cancel / reschedule / list / detail)

- **Intended result:** the booking flow is clean and practical in the editorial system: slot grid,
  `fieldset`/`legend`, inline `slot`/`reason` errors, status badge, reference ticket.
- **Files:** `appointments/templates/appointments/*.html` (6 incl. `_status_badge.html`);
  `static/css/styles.css`.
- **Reuse:** slot markup, `novalidate` + `_field.html` + `_form_errors.html`, `_status_badge.html`,
  `data-guard`. **Refine:** slot grid + ticket + badges. **Replace:** none.
- **Accessibility/responsive:** slot radios keep `value="{slot.pk}"` and a single shared hit
  target per option; status never colour-only; reference visible; errors `role="alert"`.
- **Regression tests:** appointments tests — slot `value="{slot.pk}"`, **reference** on detail,
  doctor full name on other pages, `novalidate`, double-submit guard; full suite.
- **Visual verification:** all four widths; invalid-submit path; no overflow.
- **Completion criteria:** booking family restyled with zero behaviour change; tests green.

---

### Phase 9 — Clinic self-service (availability / leave)

- **Intended result:** doctor availability/leave tables and forms match the system; confirm-delete
  pages consistent.
- **Files:** `clinic/templates/clinic/*.html` (6 files); `static/css/styles.css`.
- **Reuse:** `.table-wrap`/`.data-table`, `_field.html`, `_form_errors.html`. **Refine:** tables +
  forms. **Replace:** none.
- **Accessibility/responsive:** `scope` on headers; stacked table on mobile; labels/errors.
- **Regression tests:** clinic tests — availability shows **"Monday"** / not **"Tuesday"**; leave
  shows **"2026-02-01"** / not **"2026-03-01"**; full suite.
- **Visual verification:** four widths; table stacking.
- **Completion criteria:** clinic pages aligned; tests green.

---

### Phase 10 — Dashboards (patient / doctor / receptionist / admin / landing)

- **Intended result:** dense, practical, legible dashboards that share the editorial *type and
  colour* system **without** adopting the marketing layout. Stat cards, tables, filters,
  pagination, status actions refreshed but kept compact.
- **Files:** `dashboards/templates/dashboards/*.html` (9 files incl. `_appointment_table`,
  `_filters`, `_pagination`); `static/css/styles.css` (`.dashboard__head`, `.stat-card`,
  `.table-wrap`, `.filters`, `.pagination`, row-actions).
- **Reuse:** all dashboard partials + selectors. **Refine:** type/colour/spacing only.
  **Replace:** none. **Do not** push hero/band/editorial-cover styling into dashboards.
- **Accessibility/responsive:** `landing` shows **"No dashboard"**; doctor-without-profile shows
  **"no doctor profile"**; link to `doctor_list` present; patient full name present; booking slot
  inputs `value="{slot.pk}"`; pagination keyboard-operable; stacked tables on mobile; row-actions
  ≥32 px (kept) with visible focus.
- **Regression tests:** **all** dashboards tests (§K.5), full suite.
- **Visual verification:** four widths on each dashboard; density preserved (no marketing blow-up).
- **Completion criteria:** dashboards consistent, still dense, tests green.

---

### Phase 11 — Navigation, mobile layout & focus visibility

- **Intended result:** header/nav refined to the editorial type/colour system; mobile menu
  transition eased; **visible focus everywhere**; tap targets ≥44 px; skip link intact.
- **Files:** `templates/base.html`; `static/css/styles.css`; `static/js/app.js` (only if the menu
  transition needs a class hook — it largely exists).
- **Reuse:** existing nav/toggle/observer logic; `:focus-visible` rings. **Refine:** header,
  `.site-nav`, `.nav-toggle`, mobile panel. **Replace:** none.
- **Accessibility/responsive:** `aria-expanded`/`aria-controls` preserved; Escape→close+focus
  return; sticky header must **not** cover the focused element (add `scroll-margin-top` on
  anchors/targets); no-JS menu usable; contrast on transparent-home header.
- **Regression tests:** nav-related assertions; full suite; manual no-JS nav pass.
- **Visual verification:** four widths; keyboard tab trace; focus ring on every interactive type.
- **Completion criteria:** nav works no-JS; focus never hidden; suite green.

---

### Phase 12 — Error pages (403 / 404 / 500) · **ownership to confirm**

- **Intended result:** off-system Django default error pages replaced with `.notice`-based
  templates using the editorial shell.
- **Files:** new `templates/404.html`, `templates/500.html`, `templates/403.html`;
  `static/css/styles.css` (only if a rule is missing).
- **Reuse:** `base.html`, `.notice`. **Introduce:** the three error templates.
- **Accessibility/responsive:** link home; one `h1`; no fake content.
- **Regression tests:** existing suite (error templates are inert until `DEBUG=False`); a
  `DEBUG=False` render spot-check.
- **Visual verification:** render each template at four widths (via a DEBUG=False check).
- **Completion criteria:** error pages on-system.
- **Decision:** §5 D6 — this was deferred to "Phase 8 (security)" in `phase-7.4-ui-audit.md` §2.11;
  confirm whether 7.5 or the security phase owns it.

---

### Phase 13 — Performance & graceful-enhancement pass

- **Intended result:** motion/animation audit — **transform/opacity only**, no
  `transition: all`, correct `transform-origin`, interruptible, reveal resolves final state
  under reduced-motion, no-JS page fully readable, `will-change` not left on.
- **Files:** `static/css/styles.css`; `static/js/app.js`.
- **Reuse:** existing reduced-motion block + observer. **Refine:** transition property lists.
- **Accessibility/responsive:** reduced-motion + no-JS + reduced-data sanity passes.
- **Regression tests:** full suite; grep for `transition: all`, `outline: none` without
  replacement, infinite `animation-iteration-count`.
- **Visual verification:** reduced-motion and no-JS renders at four widths.
- **Completion criteria:** meets the `web-design-guidelines` Animation rules; suite green.

---

### Phase 14 — Final verification & `web-design-guidelines` audit

- **Intended result:** a clean audit and a documented pass; docs reconciled.
- **Files:** only fixes surfaced by the audit (expected: `static/css/styles.css`, a few
  templates); `docs/implementation-roadmap.md` (status); optional `README.md` §11 reconcile
  (documentation only).
- **Reuse/refine/replace/introduce:** per audit findings.
- **Accessibility/responsive:** full keyboard + screen-reader + no-JS + reduced-motion matrix at
  390/768/1024/1440.
- **Regression tests:** `check`, `makemigrations --check --dry-run`, `manage.py test`,
  `pytest -q`, `git diff --check`.
- **Visual verification:** all four widths on every page family.
- **Completion criteria:** audit findings resolved (or triaged with rationale); suite green;
  roadmap updated.

---

## 4. Implementation concerns (cross-cutting)

### 4.1 Font fallback & cross-platform typography
- Single `--font-display-serif` token with a full fallback chain; **system fonts only** (no
  download, ADR-020). Document the chain's behaviour per platform (Windows verified; macOS/iOS via
  `ui-serif`/Palatino; Android via Noto Serif fallback; Linux via Liberation Serif). Serif body, if
  ever used, gets extra line-height. If Phase 1's evaluation is poor, switch to **Phase 1b**
  (single sans display). Never rely on a webfont.

### 4.2 Shared editorial speciality & doctor cards
- One shared partial per entity (`_speciality_card.html`, `_doctor_card.html`) used by home,
  listing and detail pages; **do not re-split** the card system (guards the 7.4 High finding).
  Titles `<h3>`; hover ⇄ `:focus-within` parity; initial-only avatars (no photos).

### 4.3 Hero composition & the single pseudo-3D element
- Exactly **one** dimensional plate; `perspective`/`translateZ` + pointer tilt; decorative layers
  `aria-hidden`; plate carries no essential info; gated by `prefers-reduced-motion`,
  `pointer: coarse`, and min width; transform/opacity only; **no `backdrop-filter`**.

### 4.4 Existing motion utilities & reduced-motion
- Reuse `--motion-*`, `--reveal-distance`, `--hover-lift`, `.reveal` + the observer; add bounded
  depth tokens only if needed. Set explicit transition property lists. Guarantee final-state
  resolution under reduced-motion and when JS is off. **No infinite animations.**

### 4.5 Form controls, validation, empty states, auth
- Continue `novalidate` + `_field.html` + `_form_errors.html`; input radius on `--radius`;
  inline errors + focus-first-error; `_empty.html` for all empty data; auth family consistent;
  register keeps the asserted string. Inputs get meaningful `type`/`autocomplete`; labels clickable.

### 4.6 Dashboards
- Patient/doctor/receptionist/admin/landing: **type + colour only**; keep density; preserve all
  partials and asserted strings; row-actions and stacked tables intact.

### 4.7 Navigation, mobile, focus visibility
- Sticky header behaves; transparent-on-home retained; mobile toggle no-JS-usable; `aria-expanded`
  sync + Escape focus return; `scroll-margin-top` so the sticky header never covers focused
  elements; `touch-action: manipulation`; `-webkit-tap-highlight-color` intentional; visible
  `:focus-visible` everywhere.

### 4.8 Performance & graceful enhancement
- Alt-animate transform/opacity; observer not scroll listeners; reserve space (low CLS); keep JS
  tiny (existing module + at most one small gated tilt module); no new deps; no CDN; **no web
  fonts**; images (when ever added) need explicit dimensions + `loading="lazy"` below the fold.
- **No-JS:** every page readable and navigable; JS only enhances.

### 4.9 Final `web-design-guidelines` audit (Phase 14)
- Run the skill's procedure: fetch the live rule-set, read the changed files, emit terse
  `file:line` findings grouped per file, then fix. Rule areas to expect: accessibility
  (labels/`aria-label`/keyboard handlers/semantic HTML/heading order/skip link), focus states
  (`:focus-visible`, `:focus-within`, sticky header not covering focus), forms
  (`autocomplete`/`name`/`type`/clickable labels/inline errors), animation
  (`prefers-reduced-motion`, transform/opacity only, no `transition: all`, correct
  `transform-origin`), typography (`…`, curly quotes, `tabular-nums`, `text-wrap`), content
  handling (empty/long content), images (dimensions/lazy), performance, navigation/state,
  touch, safe areas, dark-mode/`theme-color`, locale (`Intl.*`, `translate="no"`), hover states,
  copy — plus the skill's anti-pattern list.

---

## 5. Dependencies between phases & decisions to validate

**Ordering dependencies**
- **P1 (typography)** underpins P2–P12 (all rely on type tokens).
- **P2 (headers/elevation)** precedes P3–P12 (shared header/measure rules).
- **P3 (cards)** precedes **P6** (listing/detail pages consume the partials).
- **P4–P5 (hero/home bands)** depend on P1–P3; independent of the app-page phases.
- **P6–P10 (page families)** depend on P1–P3; P10 depends on the firmed-up form/table styles.
- **P11 (nav)** depends on P2 (type rules) — may run anytime after.
- **P13 (performance)** and **P14 (audit)** depend on all prior phases.
- **P12 (error pages)** depends only on base + tokens; ownership unresolved (D6).

**Decisions requiring validation (resolve before/at the noted phase)**
- **D1 — Serif viability (Phase 1 gate):** confirm the system-serif stack renders acceptably
  cross-platform; if not, approve **Phase 1b** (single sans display). *Only Windows Chrome is
  measurable here; other platforms are reasoned from the CSS stack.*
- **D2 — Hero plate data (Phase 4):** decorative-only, **or** driven by existing context?
  Driving it from real availability would need new selectors/context → **out of scope** (would
  touch views). **Recommendation: decorative-only** to keep the change presentation-only.
- **D3 — Tilt JS (Phase 4):** adopt the small feature-detected tilt module, or go pure-CSS
  (e.g. hover-only)? Recommendation: adopt a tiny gated module **only** if CSS cannot deliver the
  intended feel; otherwise pure CSS.
- **D4 — Eyebrow removal scope (Phase 2):** confirm removing the label entirely vs. redesigning it
  into a structural caption.
- **D5 — Figure plate (Phase 5):** include now (photo-ready placeholder) or defer until a licensed
  image exists.
- **D6 — Error-page ownership (Phase 12):** 7.5 vs the security-hardening phase (7.4 §2.11
  deferred it).
- **D7 — Arrow disc (Phase 4/6):** keep the appended "→" on the hero CTA (meaningful direction) and
  remove it elsewhere, or drop it entirely.
- **D8 — Radius direction:** "moderate radius + whitespace" (recommended) vs. a flatter,
  rule-only treatment.
- **D9 — Dashboard editorial depth:** confirm "type + colour only" (recommended) — do **not**
  restyle dashboards toward the marketing layout.
- **D10 — README §11 reconciliation:** documentation-only update in Phase 14 (or later).

---

## 6. Regression checklist (run at the end of **every** phase)

**Commands (must all pass / match baseline)**
- [ ] `python manage.py check` → no issues.
- [ ] `python manage.py makemigrations --check --dry-run` → "No changes detected".
- [ ] `python manage.py test` → **205 OK (skipped 1)** (or better, no new failures/skips).
- [ ] `pytest -q` → **204 passed, 1 skipped** (or better).
- [ ] `git diff --check` → exit 0 (CRLF notices only).

**Contracts (unchanged)**
- [ ] URL names resolve (`reverse(...)` unaffected): website, `accounts:`, `appointments:`,
  `clinic:`, `dashboards:`, `admin:`.
- [ ] Context variables unchanged (spec §K.2).
- [ ] Form field names unchanged (spec §K.3); CSRF on every POST.
- [ ] RBAC/ownership/state transitions unchanged; no new backend code.
- [ ] Test-asserted strings still present (spec §K.5): "patients only"; "Cardiology"/
  "Dermatology" absence; "Alice Anderson"/"Bob Brown" absence; "Monday"/"15 min"; "No dashboard";
  "no doctor profile"; `doctor_list` link; patient full name; `value="{slot.pk}"`; appointment
  reference.
- [ ] No models/migrations/settings/routes/auth/forms/booking changes.

**Presentation quality**
- [ ] No `transition: all`; no `outline: none` without a `:focus-visible` replacement.
- [ ] No infinite/ambient animation; reduced-motion resolves all content to final state.
- [ ] No-JS: every page readable, nav usable, nothing stuck hidden.
- [ ] Contrast: no small `#0EA5A8` text on white; white-on-`#0B7C80` and ink-on-tint pass AA.
- [ ] No horizontal overflow at 390/768/1024/1440.
- [ ] Existing uncommitted work untouched (`git status` diff set unchanged except intended files).

---

## 7. Rollback approach (preserves all uncommitted work)

- **Never** use `git reset`, `git checkout <file>` to discard, `git clean`, or destructive
  `git stash`. Those are prohibited because the working tree holds a large, uncommitted Phase 7.x
  changeset.
- **Per-phase change log:** before editing, copy each file to be changed to the temp dir
  (`…\Temp\opencode\p75-backup\<phase>\…`, off-repo). Restore = copy back and re-verify.
- **Small phases + verification gates** make rollback a matter of reverting that phase's files
  only; because each phase is committed to *nothing*, reverting is pure file edits.
- **If a phase is abandoned:** copy the temp backups for its files back over the working copies,
  then run the §6 checklist to confirm the baseline is restored. Confirm via `git status` that the
  tracked-file diff set matches the pre-phase set.
- **If commits are later authorised:** prefer forward-fix commits or `git revert <sha>` of the
  *new* commit; never rewrite history; never touch the pre-existing changeset.
- **Non-destructive inspection is allowed:** `git status`, `git diff`, `git diff --stat`,
  `git stash list` (read-only), file copies. No state-mutating git operations.

---

## 8. Verification method (used by every phase)

- **Browser:** throwaway `playwright-core` + system Chrome in the temp dir (never a project
  dependency). **Restart a fresh dev server** before verifying (stale-server trap, §1.6).
- **Widths:** 390 / 768 / 1024 / 1440. Check: layout, column counts, no horizontal overflow,
  tap-target sizes, focus visibility, link integrity (HTTP 200).
- **States:** default, hover, `:focus-visible`, `:focus-within`, error/invalid submit, empty
  data, long content, `prefers-reduced-motion: reduce`, JavaScript disabled, touch emulation.
- **Quantitative only:** this environment has **no image input**, so verification is computed
  geometry/styles + rendered-HTML inspection — **not** perceptual screenshot review. State this
  limitation in each phase's report.

---

## 9. Definition of done for Phase 7.5

1. The hybrid identity is applied across **all** public pages and the app families, with
   dashboards still dense and practical.
2. One shared editorial card system per entity; one dimensional hero element; no ALL-CAPS eyebrow
   defaults; no appended-arrow default except where meaningful.
3. Typography is editorial (serif display + sans UI + mono data) with documented cross-platform
   fallbacks.
4. `manage.py check`, `makemigrations --check`, `manage.py test`, `pytest -q`, `git diff --check`
   all pass; no new migrations; no new dependencies.
5. Accessibility (keyboard, focus, reduced-motion, no-JS, contrast) verified at 390/768/1024/1440;
   `web-design-guidelines` audit clean (or findings triaged with rationale).
6. All pre-existing uncommitted work preserved; nothing committed or pushed.

---

*Planning artefact only. The sole file produced by this task is this document. No application
code, template, stylesheet, script, test, setting, model, migration or dependency was modified,
and nothing was installed, committed or pushed.*
