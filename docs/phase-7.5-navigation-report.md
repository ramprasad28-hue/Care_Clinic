# Phase 7.5 — Navigation, Mobile Behaviour & Focus States — Report

**Scope:** Phase 11 of `docs/phase-7.5-implementation-plan.md` (Navigation, mobile layout
& focus visibility). **Status:** complete. **Committed:** no (working tree only).

Phase 11 was a **verification-first** phase: the shared header/nav, mobile toggle, and
focus system were already carried by the uncommitted Phase 7.5 work, so the phase audited
them against the plan and closed the concrete gaps found rather than re-styling working
code.

---

## 1. Scope (derived from the plan)

From `phase-7.5-implementation-plan.md` §Phase 11 and §4.7:

- Header/nav on the editorial type + colour system; **visible focus everywhere**.
- Mobile menu transition eased; **tap targets ≥44 px**; skip link intact.
- `aria-expanded`/`aria-controls` preserved; **Escape → close + focus return**.
- Sticky header must **not** cover the focused/anchored element (`scroll-margin-top`).
- **No-JS menu usable**; transparent-on-home header retained; header contrast intact.
- Files: `templates/base.html`, `static/css/styles.css`, `static/js/app.js` (only if a
  class hook was needed).
- Completion criteria: **nav works no-JS; focus never hidden; suite green.**

**Role-based nav and authorization preserved.** Hiding a nav link is presentation only —
it is never the authorization mechanism (views/`role_required` remain the control).

> Note: the plan numbers the *implementation* phase 11; the instruction header called this
> "Phase 11 — Navigation, Mobile Behaviour and Focus States". Same phase.

---

## 2. Files changed

| File | Change | Reason |
| --- | --- | --- |
| `static/css/styles.css` | +42 / −4 lines (Phase 11 hunks) | Mobile tap targets ≥44 px, `touch-action`, motion-token alignment, anchor `scroll-margin-top`. |
| `website/tests.py` | +75 lines (`SharedNavigationTests`, 9 tests) + `make_user` helper | Lock the nav structural contract (landmarks, skip link, toggle wiring, role links, POST logout). |
| `templates/base.html` | **inspected, unchanged** | Already conforms (skip link, `aria-controls`/`aria-expanded`, role-aware links, POST logout). |
| `static/js/app.js` | **inspected, unchanged** | Mobile-menu class hooks + Escape + focus-return already implemented; no change required by the plan. |

No other file was touched; no business logic, route names, or destinations changed.

### CSS hunks (line numbers as of this pass)

- **`197`** — new rule `[id] { scroll-margin-top: calc(var(--header-h) + var(--sp-4)); }`
  so every fragment target (skip link, in-page anchors) scrolls clear of the sticky header.
- **`351`/`361`** — `.nav-toggle`: `min-height/width: 2.75rem` (44 px), `touch-action:
  manipulation`, and a tokenised `border-color`/`color` transition.
- **`406`** — `.site-nav__link`: `touch-action: manipulation` + transition aligned to
  `var(--motion-fast) var(--ease-standard)` (was `0.15s ease`).
- **`1770–1776`** — within `@media (max-width: 900px)`, `.site-nav__link` gets
  `display:flex; align-items:center; min-height:2.75rem` (48 px measured).
- **`1787–1793`** — mobile `.site-nav__account .btn` / `.link-button`:
  `width:100%; min-height:2.75rem` (44 px measured), link-button centred.

---

## 3. Nav & mobile behaviour (verified)

Structural contract in `templates/base.html` (unchanged, now tested):

- Skip link → `#main-content`; `<main id="main-content">` landmark present.
- `button.nav-toggle[type=button][aria-expanded=false][aria-controls=site-nav]`, label "Menu".
- `<nav id="site-nav" aria-label="Primary">`; active link uses `aria-current="page"`.
- Role-aware links: anonymous `Specialities`/`Doctors`; authenticated adds
  `Dashboard`/`My appointments`; doctor adds `Availability`/`My leave`; staff adds
  `Django admin`. Logout is a **POST form with CSRF**.

Mobile open/close (Chromium, 390 px, real click + key events):

| Step | `#site-nav` display | `aria-expanded` | note |
| --- | --- | --- | --- |
| initial | `none` | `false` | collapsed with JS |
| after toggle click | `flex` (+`is-open`) | `true` | panel shown |
| after **Escape** | `none` | `false` | focus returns to the toggle (`document.activeElement` = `.nav-toggle`) |

Clicking a link inside the open panel also closes it at ≤900 px
(`app.js`, `matchMedia("(max-width: 900px)")`). Breakpoint matches the CSS (`900px`).

---

## 4. Accessibility & keyboard

- **Escape** closes an open menu and returns focus to the toggle (verified above).
- Focus is never lost on close: Escape → toggle; link click → navigates; toggle click →
  toggle retains focus.
- **Tab trace at 1440 px:** `Skip to main content` → `Care_Clinic` (brand) → `Specialities`
  → `Doctors` → `Log in` → `Register` → `Book appointment` → `Book an appointment` — every
  stop resolves to a real element with a visible ring (no dead/focusable-but-hidden stops;
  the mobile toggle is `display:none` at ≥901 px and is not a tab stop).
- All nav interactive elements are links/buttons with visible accessible names
  ("Menu", link text, "Skip to main content").
- Skip link is the first tab stop and becomes visible on focus (`.skip-link:focus`).

## 5. Focus visibility

- Global `:focus-visible { outline: 3px solid var(--focus-color); outline-offset: 2px }`;
  measured ring on a nav link: **`3px rgb(11, 124, 128)`** (`#0b7c80`).
- On the transparent homepage hero header (≥901 px) `:focus-visible` outline switches to
  `--brand-050` (`rgb(232, 248, 248)`) so it stays visible on the dark hero — measured on
  the brand/links during the tab trace.
- No `outline: none` without a replacement: the only `outline` suppression is
  `input/select/textarea:focus` (`styles.css:892` region), which substitutes a
  `0 0 0 3px rgba(14,130,141,.18)` box-shadow ring — intentional, pre-existing, unchanged.

## 6. Responsive (390 / 768 / 1024 / 1440)

| Width | Header | Toggle | Primary nav | Overflow |
| --- | --- | --- | --- | --- |
| 390 | sticky (`63 px`) | visible, 44×88 px | collapsed (`none`) | 0 |
| 768 | sticky (`73 px`) | visible, 44 px | collapsed (`none`) | 0 |
| 1024 | sticky -or- `absolute` on home hero | hidden | `flex` | 0 |
| 1440 | sticky -or- `absolute` on home hero | hidden | `flex` | 0 |

- **Transparent-on-home retained:** on `home`, `.site-header--hero` is `position:absolute`,
  transparent, desktop-only (`@media (min-width: 901px)`); on all other pages and all
  mobile widths the header is opaque/sticky.
- **Tap targets ≥44 px on the mobile touch surface:** toggle 44 px; open-menu nav links
  48 px; mobile account buttons/link-button 44 px. Desktop pointer targets stay as designed
  (~33–34 px) — 44 px is applied only to the mobile navigation surface, per plan intent.
- One `<h1>` per page at all widths; no horizontal overflow at any width.
- Reduced-motion and menu-open states produce no horizontal overflow.

## 7. Progressive enhancement (no JS)

With `Emulation.setScriptExecutionDisabled` at 390 px:

- `<html class="no-js">` retained; `#site-nav` is `display:flex` (menu **fully visible**),
  2 public links present; `.nav-toggle` is `display:none` (no dead control).
- CSS already guarantees this: `html:not(.js) .site-nav { display:flex }` and the toggle is
  only shown under `.js`. Nav therefore works without JavaScript, as the architecture
  requires. Verified end-to-end for `home` and `speciality_list`.

## 8. Reduced motion

With `prefers-reduced-motion: reduce` emulated at 1024 px: computed
`transition-duration` / `animation-duration` collapse to `0.001ms` (nav links and menu
open/close included). The reduced-motion block also disables the `.skip-link` transition
and decorative reveals; menu show/hide resolves instantly to its final state.

## 9. Tests & completion checks

| Command | Result |
| --- | --- |
| `manage.py check` | System check identified no issues (0 silenced) |
| `manage.py makemigrations --check --dry-run` | No changes detected |
| `manage.py test` | **228 tests, OK (skipped=1)** — 291.7 s |
| `pytest -q` | **227 passed, 1 skipped** — 281.1 s |
| `git diff --check` | exit 0 (only pre-existing LF→CRLF warnings) |

- Phase 11 added `website.tests.SharedNavigationTests` (9 tests): skip link + main
  landmark; progressive-enhancement hook (`class="no-js"` + inline de-classer);
  mobile-toggle wiring (`type=button`, `aria-expanded`, `aria-controls`, `id`, `aria-label`);
  anonymous primary links + absence of private ones; `aria-current` active state;
  patient / doctor / staff role link sets; POST logout form with CSRF.
- Baseline before Phase 11 was 219 tests; **+9 = 228**.
- The single skip is the pre-existing MySQL-only concurrency test
  (`appointments/tests.py:764`, `@unittest.skipUnless(...)`) — ADR-003 selects SQLite only,
  so it does not validate MySQL/InnoDB.

## 10. Not done / follow-ups

- **No implementation change was needed in `templates/base.html` or `static/js/app.js`** —
  the menu transition already used class hooks (`is-open`/`is-closing`) with
  `var(--motion-base) var(--ease-out)`; the audit deliberately added no churn there.
- Desktop pointer targets remain ~33–34 px (unchanged design); only the mobile navigation
  surface was raised to ≥44 px, matching the plan's "mobile layout" framing.
- The shared `partials/_field.html` `aria-describedby` dangling-reference limitation
  (documented previously) is out of Phase 11 scope and unchanged.
- No perceptual/screenshot review performed (the model cannot read image input); all
  claims above are DOM/computed-style measurements.
- Phase 12 (error pages) not started — per instruction, stop after Phase 11 for review.

### Completion criteria

- **Nav works no-JS** — verified (progressive-enhancement pass).
- **Focus never hidden** — verified (`[id]` scroll-margin clears the sticky header:
  target top `63 px` = header height; visible `:focus-visible` ring on every nav stop).
- **Suite green** — `manage.py test` 228 OK (skipped=1); `pytest -q` 227 passed, 1 skipped.
