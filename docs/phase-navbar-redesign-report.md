# Phase — Navbar redesign (Hospic-inspired shared navigation)

Status: Proposed (awaiting human review) · Date: 2026-10-19
Scope: shared site navbar only. The approved hero (phase 7.5 revision 2) and footer redesign were left untouched apart from their interaction with the header (see "Scrolled state").

## Goal

Match the quality bar set by the Hospic reference for the top of the page: a shared, calm, trustworthy navbar that is transparent over the homepage hero, collapses to a light sticky bar on interior pages, gains a fixed dark-navy scrolled state on the homepage, and exposes a rich, DB-driven "Specialities" mega menu on desktop. All previous invariants kept: no new dependencies/interfaces (ADR-020), no model/migration changes (ADR-006), templates stay "dumb" with logic in views/tags/CSS.

## What was changed

### New files

- `templates/partials/_nav_mega_panel.html` — the desktop/mobile mega-menu panel partial. Loads the same `footer_specialities` tag introduced for the footer (reused rather than duplicated DB access), and guards every image with `static_exists`.

### Modified files

- `templates/base.html` — rebuilt the navbar:
  - Brand (teal plus mark) left; centred nav links: Home, About (`{% url 'home' %}#about-heading`, anchor exists in `home.html`), Specialities (mega), Doctors.
  - Account area right: for anonymous users Log in (text link) / Register (outline pill) / Book appointment (primary pill); for authenticated users role-aware links (Dashboard, My appointments, Availability, My leave, Django admin) plus email + role caption next to Book appointment / Log out (existing routes unchanged).
  - Specialities is an `li.nav-mega` containing: a plain link (`a.nav-mega__plain`, shown only when JS is unavailable — progressive enhancement), a trigger `button.nav-mega__trigger` with `aria-expanded` + `aria-controls="nav-specialities-menu"` + chevron, and the included panel.
  - Both header Book actions now use the existing `btn btn--primary btn--sm btn--arrow` + `.btn__disc` circular-arrow treatment so the navbar matches the hero CTA language.
- `static/js/app.js` — added two small behaviours (no framework):
  - Mega menu: open/close on trigger click, close on Escape (then `trigger.focus()`), close on outside click, close when a panel link is clicked on desktop (`matchMedia("(min-width: 901px)")`).
  - Homepage scrolled state: `.site-header--hero` gains `.is-scrolled` after the header clears the hero (`hero.offsetHeight - header.offsetHeight`), toggled from passive `scroll`/`resize` listeners.
- `static/css/styles.css` — added the mega/scrolled styles (hero and footer blocks untouched):
  - Desktop (`> 900px`): `.nav-mega { position: static }` makes the panel positionable; open panel (`.js .nav-mega__panel.is-open`) is absolutely centred under the header (`width: min(1128px, calc(100vw - 2rem))`), white surface, radius-lg + shadow-lg; 2-column item list with photo tiles + line-clamped descriptions; right-side feature card on the brand tint; "View all specialities" divider foot row.
  - Homepage transparent header keeps white links over the hero; scrolled state (`.js .site-header--hero.is-scrolled`) becomes `position: fixed` on `rgba(15,45,49,0.9)` + backdrop blur — consistent with the approved footer navy.
  - Interior pages get the light sticky header with dark links (existing base styles).
  - Mobile (`≤ 900px`): existing drawer; Specialities becomes a full-width trigger row and the panel renders inline unstyled (1-col list, smaller tiles, aside hidden, foot row kept).

## Bugs caught during verification (all fixed)

1. **Feature-card image missing.** `{% static 'img/about/waiting-area.jpg' as feature_photo %}` produces an *absolute* URL, which `static_exists` then treats as a filesystem path — always false, so the card silently disappeared. Fixed by using `{% with 'img/about/waiting-area.jpg' as feature_photo %}` (relative path) and applying `{% static %}` only at the render site. The per-item tiles already used the correct `{% with %}`-relative pattern.
2. **Unreadable trigger.** The UA `buttonface` background made `.nav-mega__trigger` a grey box over the photo. Fixed with a button reset (`background: transparent; border: 0; cursor: pointer; font: inherit;`).
3. **Duplicate row on mobile.** `html.js .nav-mega__plain { display: none }` was unscoped and lost to the later mobile `.site-nav__link { display: flex }` drawer rule, showing both the plain link and the trigger. Re-scoped the hide rule so only one row shows per mode.
4. **Unclosed `{% with %}` (caught by the suite, not the eye).** The first full `pytest` run failed 84 tests with `TemplateSyntaxError: Unclosed tag on line 5: 'with'` in `_nav_mega_panel.html` — an outer `{% with %}` left open after the feature-card rework. Earlier scratch renders happened to predate the edit, which is why browser checks looked fine; the test suite caught what the screenshots could not. Fixed and all tests pass again.

## Verification

- `python manage.py check` → 0 issues; `makemigrations --check --dry-run` → no changes.
- Full suite: **228 OK (skipped=1) via `manage.py test`, 227 passed / 1 skipped via pytest** (after fix 4; the 84 failures were the single unclosed tag).
- `git diff --check` clean (only pre-existing CRLF warnings); nothing staged/committed.
- Scratch QA harness (temp dir, not committed): `navqa.mjs` — 19/19 interaction checks pass, 0 console errors: trigger toggles `aria-expanded`, 5 speciality items with tiles, feature CTA href, open/close/Escape (focus returns to trigger)/outside-click, panel layered under header, all images `complete && naturalWidth > 0`, zero horizontal overflow in closed/open/scrolled/mobile states, mobile drawer with expandable Specialities, light-page sticky header, scrolled fixed navy bar.
- Screenshot review (inspected, not assumed): `nav_mega_1440`, `nav_mega_1024` (panel, 2-col links, teal feature card, pill CTAs — clean), `nav_mobile_closed_390` (teal mark + Menu button — clean), `nav_mobile_open_390` (5 touch rows + View-all divider, no duplicate — clean after fix 3), `nav_scrolled_1440` (fixed navy bar coherent), `nav_light_1440` (light sticky header on interior page), authenticated variant `home_auth.html` rendered via `force_login` (receptionist): Home active pill, role-aware links, email + "Role: receptionist", Book appointment + Log out — all correct.

## Decisions & limitations

- **Mega menu opens on click AND desktop pointer hover** — hover was added after the phase was proposed (see Revision 3); click/keyboard remain the accessible baseline, hover is a progressive enhancement only.
- **No focus trap inside the panel**: Escape and outside-click close it and return focus to the trigger; a full trap would over-engineer a non-modal surface. Flagged for the human review pass.
- **DB-driven, hard-coding avoided**: the panel and mobile list reuse `footer_specialities`; a speciality without a card image simply renders without a tile rather than fabricating one.
- **Imagery honesty/licensing unchanged**: the panel reuses only the seven licensed Pexels assets already documented in `imagery-licensing.md` (feature card: waiting-area.jpg; tiles: `<slug>-card.jpg`).
- Any contact info remains out of scope (project truthfully has none — `CustomUser.phone` is the only field, so the panel/footer link to pages, never a fabricated phone/address).
- Known pre-existing issue, untouched per prior decision: `_field.html` dangling `aria-describedby` under Django 5.2.
- Dev server (PID 25244) running on 127.0.0.1:8000 per user's earlier request; templates now verified against the real render path.

## Revision 4 — Specialities interaction fix + Doctors mega menu (2026-10-19, user-directed)

Human review reported two issues: (1) clicking Specialities "does not work as expected; it looks like a static button", and (2) the Doctors item should get its own large mega menu with a healthcare image column.

### Confirmed root cause of the Specialities problem (verified live, not assumed)

Probed the **running server** (dev server PID 25244 verified as the only listener on 8000, `manage.py runserver`, started 2026-10-19 08:11:55 — assets and templates confirmed fresh, no stale copy) with a real browser driven through CDP `Input.dispatchMouseEvent`. Findings: app.js and styles.css load, the trigger/`aria-controls` IDs match the DOM, no console errors — and then, with genuine pointer input: **hover opened the panel; the click on the trigger then toggled it shut.** A visitor who moves the mouse to Specialities and clicks watches the menu vanish, so the click feels dead; the earlier bad gate (`prefers-reduced-motion` disabling hover) could make it feel worse for those users.

### Specialities fix (`static/js/app.js` rework, shared with the new menus)

- **Pinned state semantics**: a click while hover-open now *pins* the menu (stays open — the panel can no longer vanish under an active pointer); a further click closes it; a click from closed opens it pinned, so it survives the pointer drifting away until the user closes it (click again / Escape / outside click / opening the other menu).
- **Reduced motion no longer interacts with the menu at all** — the `prefers-reduced-motion` condition was removed from the hover gate; it now only affects animation (there was none to suppress).
- Both menus share one controller pattern; **opening one menu closes the other**; Escape returns focus to the trigger; outside click closes; desktop panel link clicks close the menu; keyboard Enter/Space activates the trigger (real `Input.dispatchKeyEvent` verified).
- The Specialities panel already contained the required "View all specialities" link to the listing route (unchanged).

### Doctors mega menu (new)

- `website/templatetags/clinic_nav.py` — added `nav_doctors`: one query via the existing `Doctor.objects.public()` manager (same visibility rules as the doctor listing: active user + active speciality + accepting appointments), `select_related("user", "speciality")`, capped at six. No extra views, no booking-logic change, no hardcoded names.
- `templates/partials/_nav_doctors_panel.html` (new) — mirrors the Specialities menu's grid: left column of real doctors (monogram avatar per the existing initials-fallback convention, real name, real `speciality.name · qualification`), a truthful empty-state line if none exist, a right-side feature column with a locally stored licensed photograph (`img/home/hero-main.jpg`, guarded by `static_exists`, reusing only manifest-documented assets — a generic welcoming image, never presented as a specific doctor; no invented qualifications/testimonials/claims), and a "View all doctors" foot link to the existing listing.
- `templates/base.html` — the Doctors `<li>` became a `.nav-mega` item with the same non-JS plain link (with its `aria-current` logic preserved), the accessible trigger (`aria-controls="nav-doctors-menu"`), and the included panel.
- `static/css/styles.css` — small additions reusing every existing mega class: `.nav-mega__avatar` sizing for the panel lists (desktop 2.6rem / mobile 2.9rem) and a `.nav-mega__empty` style.

### Verification — the actual running application, real pointer + keyboard input

`liveqa.mjs` (scratch QA harness, not committed) drove **real CDP mouse/keyboard events against `http://127.0.0.1:8000/`**: **37/37 checks pass, zero console errors**, covering all 15 required behaviours at 390/768/1024/1440:

- hover Specialities opens · click keeps it (the fix) · second click closes · pointer into panel stays · leaving closes · Escape closes + focus returns · keyboard Enter opens · opening Doctors while Specialities is pinned switches menus · Doctors hover/click toggle · clicking a doctor navigates to its real detail page → `location.pathname` asserted against the link's own `href` · "View all doctors" → `/doctors/` · speciality click → real detail page · "View all specialities" → `/specialities/` · outside-click closes · reduced-motion page (`reducedMotion: true`) still opens via hover and pins via click · 390/768 tap-to-expand inside the drawer with every link reachable and zero overflow.
- Screenshot review (inspected): Specialities panel open desktop (`live_specs_open_1440`), Doctors panel open desktop (`live_doctors_open_1440`), mobile Specialities expanded (`live_mobile_specs_390`), mobile Doctors expanded (`live_mobile_doctors_390`). Both desktop panels are the same balanced 1128px rounded composition under the navbar; hero and footer untouched in every shot.
- Two test-script bugs found during this QA were artefacts, not product bugs: a `sel` not passed to the eval sandbox, and QA click points that landed inside the fully open panel (panel reaches y≈632 at 1440 — panel bottom 632 was measured and is the expected 1128×560 geometry shared with the Specialities menu).
- `manage.py check` 0 issues · `makemigrations --check --dry-run` no changes · SharedNavigation tests 9/9 OK · full suite **227 passed / 1 skipped** (pytest) · `git diff --check` clean · status line count 76 (one new partial; all pre-existing modifications preserved; nothing staged/committed).

### Remaining limitations

- The Doctors panel caps at six doctors; a busy roster links through "View all doctors" rather than an endless panel.
- The Doctors feature photo reuses the licensed hero asset; a dedicated menu photograph would need a new licensed addition (kept to zero new assets in this phase).
- The hover pin semantics mean a hover-opened menu stays open until closed by the user — standard disclosure-menu behaviour, but worth human confirmation.

## Revision 3 — Desktop hover behaviour (2026-10-19, user-directed)

The human review asked for the Hospic reference interaction: the Specialities mega menu must open on desktop pointer hover while everything else (approved navbar/hero/footer design, click activation, accessibility, mobile tap behaviour) stays intact.

### Implementation (`static/js/app.js`, `static/css/styles.css` — no template changes)

- **Hover region = the `li.nav-mega` itself.** The panel already lives inside the LI, so moving the pointer from the trigger into the panel never counts as "leaving" the region for pointer enter/leave purposes — the pointer can't lose the menu mid-travel.
- `pointerenter` on the combined region opens the menu and cancels any pending close; `pointerleave` schedules a short, cancellable close (260 ms) so heading through the small gap below the trigger (or a diagonal path) never flickers the panel open/shut.
- **Hover is narrowly gated**: only `pointerType === "mouse"` AND `min-width: 901px` engages hover — touch devices and the mobile drawer are structurally unaffected, and `prefers-reduced-motion` users keep click/keyboard activation.
- **CSS hover bridge** (`.js .nav-mega__panel.is-open::before`, an invisible 1rem strip above the panel): pointer travel through the gap between the header edge and the panel still lands inside the menu region, so the close-delay is a safety net rather than a dependency. Purely decorative overlay — no layout shift (the panel is absolutely positioned).
- **Click activation retained**: the trigger still toggles on click/Enter/Space (a hover-opened menu closes on click, as before).

### Accessibility (unchanged semantics)

`aria-expanded`/`aria-controls` on the trigger still drive all state (hover and click go through the same `setOpen`), Escape closes and returns focus to the trigger, outside-click closes, keyboard users activate the button and Tab into the panel links — nothing about the menu is hover-only.

### Verification (real pointer input, not synthetic JS)

- Extended the scratch QA harness to drive **actual mouse events via CDP `Input.dispatchMouseEvent`**: hovering the trigger opens the menu ("REAL pointer hover opens menu"), moving the pointer into the panel keeps it open (checked after 600 ms), pointer leaving the combined region closes it (after the grace delay). Same real-hover test repeated at 1024. New 768 block: drawer present, tap expands the panel, no overflow; 390 block gained "mega stays closed before any tap" (no hover side-effects).
- **27/27 checks pass, zero console errors** (was 19/19 pre-revision).
- Screenshot review (inspected, captured in the required order): desktop navbar closed (`nav_closed_1440`), pointer hovering Specialities with the panel just opened (`nav_hovertrigger_1440` — chevron flipped, trigger highlight, no layout shift), panel fully visible with pointer inside it (`nav_hover_1440` — active row tinted, all 5 links + feature card), mobile Specialities expanded (`nav_mobile_open_390`). Widths covered: 390, 768, 1024, 1440.
- `manage.py check` 0 issues; SharedNavigation tests 9/9 OK; full suite **227 passed / 1 skipped** (pytest); `git diff --check` clean; status line count unchanged at 76 files (no new files).

## Revision 5 — Header alignment: brand + navigation on one desktop row (2026-10-19, user-directed)

Human review issue 3: at desktop widths, **authenticated** headers were not aligned as required — the navigation row wrapped below the brand, and the requirement forbids the Specialities/Doctors labels from sitting on the line above the logo.

### Root cause (measured, not assumed)

Measured content widths per auth state with a scratch bounding-rect script (`hdrmeasure.mjs` / `hdrsums.mjs`) over 5 viewports (1440 / 1280 / 1024 / 768 / 390) × 5 states (anonymous, patient, receptionist, doctor, admin; scratch pages rendered via `manage.py shell` with `force_login`, roles in caps). Facts:

- Anonymous fits the single row everywhere ≥ 1024 (deficit −302 … −84 px, up to +17 at 1280).
- Authenticated with Staff model ("Django admin", doctor console links, identity block, Book + Log out) needs up to **1298 px** against a 1160 px container inner width at 1440 (942 px at 1024) → `.header-inner { flex-wrap: wrap }` pushed the nav to a second row; doctor/admin cannot fit at 1024 even fully compacted.

### Implementation (`templates/base.html`, `static/css/styles.css`, `static/js/app.js`)

- Header tag now carries `site-header--dense` when `user.is_authenticated`.
- **Desktop single-row block (≥ 901 px)**: `.header-inner` nowrap, brand `flex:none`, nav `min-width:0; flex:1`, links nowrap, account `min-width:0`, **email truncation ladder** (`max-width: 14ch` / 12 ch ≤ 1279 → 10 ch ≥ 901 for dense bars only; ellipsis) — identity (email + role) always visible, never hidden on desktop.
- **Progressive compaction per requirement 5**: at ≤ 1440 px dense bars first drop the *nonessential staff console shortcuts* — `Django admin` (`.nav-admin`) and doctor `Availability` / `My leave` (`.nav-doctor-tools`) get classes in `base.html` and are hidden in that band; patient-facing links and identity are preserved. These links remain full-size ≥ 1441 px and inside the dense drawer.
- **Dense drawer band (901–1180 px, dense only)**: full copy of the mobile drawer rules scoped to `.site-header--dense` (nav column, `is-open`/`is-closing` animations, stacked account, full-width mega triggers/panels, aside hidden — email `max-width` reset so identity is reachable). Anonymous visitors keep the desktop bar here (no regression). `app.js` drawer-close-on-link-click media widened from `(max-width: 900px)` to `(max-width: 1180px)` (safe for anon: `closeNav` early-returns when nothing is open).
- Two visual wrap regressions caught and fixed while iterating: link labels and button texts need `white-space: nowrap`, and mega triggers need `display:inline-flex` so chevrons don't drop under labels.
- Edit discipline note: during the base.html header-tag edit a stray placeholder/`</header>` briefly appeared and was removed in the next edit; a `.nav-mega__tile {` opening line was clipped once and restored — both verified present/clean afterwards.

### Verification (automated + visual, not assumed)

- `hdrverify.mjs` (scratch): **83/83 checks pass** — per state × width: header mode correct (bar vs drawer), brand + nav + account aligned on one row via vertical midpoints (gap ≤ 5 px), no brand/nav overlap, **no hidden link-row squeeze** (sum of `li` widths ≤ row width — catches content melting into the account segment), no email text clipped (`scrollWidth ≤ clientWidth`), account inside viewport, no horizontal overflow, drawers open/close with expandable megas (Specialities + Doctors) and no `console` errors each run. 15 px final margins in the tight bands (1280 admin, 1024 receptionist).
- Screenshot review (inspected): `hdr2_1440_patient_bar`, `hdr2_1280_admin_bar`, `hdr2_1024_patient_closed`, `hdr2_390_patient_drawer`.
- Behavioural regression: `liveqa.mjs` against the **running server** — **37/37, zero console errors** on all 15 required behaviours at 390/768/1024/1440 anonymous + patient (the 1024 patient page now uses the dense drawer by design; its 15 required behaviours still pass).
- Static regression gate: `manage.py check` 0 issues; `makemigrations --check --dry-run` no changes; SharedNavigation tests **9/9 OK** (CSS-hiding `Django admin` does not remove it from the DOM); full pytest **227 passed / 1 skipped**; `git diff --check` clean; `git status --porcelain` unchanged at 76 files.

### Remaining limitation (flagged for human review)

Between 901 and 1180 px staff users get the drawer instead of the desktop bar, and the staff console links hide at ≤ 1440 px — both are the sanctioned "compact nonessential items before wrapping" trade-off; the alternative was rewriting the bar's information architecture (rejected as out of scope without a decision).

_Environment note: the original dev-server process (PID 25244) died between revisions; replaced with a fresh `manage.py runserver` instance on 127.0.0.1:8000 (new PID 13820) — same user-sanctioned exception._

## Revision 6 — Doctor/Admin identity overlap on wide desktops (2026-10-19, user-directed)

Human review found the **Doctor** authenticated header colliding with the primary nav: the account email/name and the "Role: Doctor" lines were painted over by nav links.

### Root cause (measured, not assumed)

Revision 5 verified only viewports up to 1440 px experientially and up to ~1211 px in the follow-up check, and both organisations used live role logins only up to 1440. On wide desktops the錒 dense bar gains `.nav-doctor-tools` (Availability, My leave) and `.nav-admin` (Django admin) again; those links were **never verified at > 1440**, and the vertical budget is fixed: `.container` caps at `1160px`, so the row interior never grows with the viewport. Live CDP measurement (logged-in QA users, `measure.mjs`, widths 1181/1280/1366/1440/1500/1536/1664/1920):

- Doctor ≥ 1500 px: nav content right edge 1116–1326 px vs account left edge 1003–1213 px — up to **113 px overlap**; the identity block's email was crushed to 40 px (unreadable "qa-n…").
- Admin ≥ 1500 px: same collision for "Django admin" (up to 71 px overlap).
- Anonymous/Patient: clean at every width (the bug was strictly the ≥ 1441 px staff band).

Secondary defect found while fixing: the Rev-5 hide rule scoped to `901px..1440px` also hid the console links **inside the 901–1180 dense drawer**, contradicting Revision 5's own claim that they "remain reachable inside the dense drawer".

### Fix (`templates/base.html`, `static/css/styles.css`; `app.js` reverted to its approved state)

Rather than keep recompressing an impossible row (staff rows need ~1298 px vs a ~1086–1160 px inner width), the staff console became one accessible grouping instead of floating loose links — the sanctioned "Workspace/More" route:

- **base.html**: staff headers (Doctor or Administrator) now render a single `li.nav-mega.nav-workspace` with a `nav-mega__trigger` button — same trigger/panel/hover/Escape/outside-click controller as Specialities/Doctors (no JS changes). The panel (`role="region" aria-label="Workspace menu"`) lists **Dashboard, My appointments**, plus **Availability + My leave** for doctors and **Django admin** for administrators, each with the correct `aria-current` logic. Patient headers keep their approved top-level Dashboard/My appointments links byte-identical. Anonymous headers untouched.
- **styles.css**: compact right-anchored panel styles (`.nav-workspace__item`, container-right-edge alignment at ≥ 1181 px), and the old `901px..1440px` hide block — which silently removed the console links even from the drawer — was retired. `.nav-doctor-tools`/`.nav-admin` top-level links are gone with the grouping (their content lives inside the menu), so no element is hidden by CSS anywhere.
- Header rows stay single-row ≥ 1181 px exactly as approved; 901–1180 keeps the approved dense drawer (Workspace appears there as a stacked expandable group); ≤ 900 px keeps the mobile drawer.

### Verification (rendered DOM + real browser, not assumptions)

- **navfixqa.mjs (new harness vs running server): 335/335 checks, zero console errors** — 14 widths (390, 768, 901, 1024, 1100, 1180, 1181, 1211, 1280, 1366, 1440, 1500, 1536, 1920) × 4 states: single-row bars (vertical midpoints), `navRight − accLeft ≤ 0` everywhere, account inside viewport, identity not clipped, patient links preserved, drawer open/close + link-click closes, Workspace section reachable inside drawers, bar-mode Workspace opens via click AND real `Input.dispatchMouseEvent` hover, Escape closes, panel below trigger and right-anchored, required staff/patient screenshots.
- **Repair confirmations (same harness pre/post):** before the fix Doctor/Admin ≥ 1500 px failed exactly the reported way (overlap up to 113 px, email width 40 px); after the fix every state holds 55–110 px slack and the email renders at its normal 10–14 ch truncation ladder (102 px), while patient/anon rows are numerically unchanged pre/post.
- **pairwise.mjs (independent overlap oracle): 40/40 states with zero intersecting header element pairs** across 4 states × 10 widths — supersedes two heuristic misfires of the legacy `hdrverify.mjs` squeeze check (79/83; its two failures rely on the pre-Revision-6 DOM shape and the grouping this fix intentionally introduced).
- **Regression surface:** `liveqa` 37/37 and `navqa` 27/27 (prior behaviours incl. mega menus + drawers, zero console errors); `manage.py check` 0 issues; `makemigrations --check --dry-run` no changes; full pytest **227 passed / 1 skipped** (267 s); `git diff --check` clean (CRLF advisories only); `git status --porcelain` 78 lines — the +1 vs 77 is the F3 report file from the previous phase; no new files from this phase.
- QA hygiene: three `qa-nav-*` probe users were created via `manage.py shell`, driven through the real login flow, and **deleted afterwards**; durable users (admin@care.com, three seeded doctors, patient email) untouched.

### Screenshots (inspected while iterating: C:\Users\Ramprasad\AppData\Local\Temp\opencode\phase-navdoc\shots\)

Desktop bars: `nf_doctor_1920`, `nf_doctor_1440`, `nf_doctor_1211`, `nf_admin_1920`, `nf_admin_1211`, `nf_patient_1440`, `nf_patient_1181`, `nf_anon_1181`, `nf_anon_1920`; workspace interaction: `nf_doctor_1280_wsopen`, `nf_admin_1280_wsopen`; narrower: `nf_doctor_1024` (collapsed drawer bar), drawer states `nf_doctor_{1024..768}_drawer` etc. Before/after evidence: `st_doctor_1500.png` / `st_admin_1920.png` show the reported collision pre-fix.

### Changed trade-offs (flagged for human review)

- Staff console links (incl. Dashboard/My appointments for staff) are one interaction deeper (open Workspace → click) on desktop bars ≥ 1181 px; they stay flat and one click away inside mobile and dense drawers. This is the sanctioned grouping; if a role needs one-tap direct access, that is an information-architecture decision for a later phase.
- The "email truncation ladder" values are unchanged; no element relies on absolute positioning or overflow-hidden to fix the collision — the row itself fits.

_Environment note: verified on the live dev server (PID 28656) on 127.0.0.1:8000 throughout; no server restart was needed._

## Revision 7 — post-review navdefects: Workspace menu position + drawer readability (2026-10-20, user-directed)

Human review of Revision 6 reported two defects:

1. **The Workspace dropdown "opens far right, detached from the Workspace nav item"** — it appeared over the booking panel instead of under its trigger.
2. **On the mobile/tablet menu (~1068 px) the text was invisible** — an expanded white panel showed blank rows; only "Book appointment" remained visible.

### Root causes (measured before any change, `r7-inspect.mjs`, `r7qa.mjs`)

1. **Workspace panel anchoring.** The Revision 6 override anchored the open panel to the *container's* right edge: `@media (min-width: 1181px) { left: auto; right: calc((100% - min(var(--container), 92vw)) / 2) }`. Because `li.nav-mega { position: static }` makes `.site-header` the containing block, the panel parked at the container edge — measured **241–242 px right of the trigger** (1280/1440: trigger left 650/731 vs panel left 892/972). The user-requested parking anchor in the prior revision assumed it would sit near the trigger; in practice the trigger is ~240 px left of where the panel landed.
2. **White-on-white drawer text on the home hero header.** `home.html` sets `site-header--hero` **unconditionally**, so authenticated home visitors get `site-header--hero site-header--dense`. The hero white-text rules are scoped `@media (min-width: 901px)` (links rgba(255,255,255,.92), white brand/user/link-button, translucent-white `btn--secondary`) — exactly the dense drawer band. The drawer surface is `var(--paper)` (white): live measurement showed `links rgb(255,255,255)` on `drawer background rgb(255,255,255)` at 1024/1068 — invisible. At ≤ 900 px the hero rules do not apply, which is why the same drawer stays readable on phones (visible in the before-shots).

### Fix (`static/css/styles.css` only; templates, app.js, models, URLs untouched)

1. **Workspace menu:** `li.nav-workspace` is now `position: relative` (it becomes the dropdown's containing block; the LI boxes the trigger exactly). The `≥ 1181 px` override is replaced with `left: 0; right: auto; top: 100%; transform: none; width: min(328px, calc(100vw - 2rem))` — **left edges aligned with the trigger, opening immediately below it** (or slid just below the trigger line, per measurement `panT == trigB == 56`), never parked near the account actions and never off-canvas. The shared trigger/panel/hover/Escape/outside-click controller is untouched.
2. **Drawer contrast:** inside the `901–1180` dense-drawer block, equal-specificity, later-in-file hero restorations scoped to **`.site-header--hero.site-header--dense`** (dense-scoped so the anonymous bar, whose links are visible over the hero photo at these widths, keeps its approved white treatment): nav links `var(--ink-700)`, hover/current teal pill, email `var(--color-text)`, role/muted `var(--brand-700)`, and the drawer's Log out (`btn--secondary`) restored to the standard paper/ink bordered look. The `.brand` **keeps** its hero white — in this band the brand lives in the transparent bar over the photo (the drawer has no brand) and must also read on the navy `.is-scrolled` bar (first fix attempt darkened it; reverted after screenshot review).
   - Root cause residual: the old "anonymous-only" band rule `.site-user { display: none }` (documented for anonymous, which has no `.site-user` element at all) in fact hid the **authenticated drawer's identity block**; it was removed, so email/role now render in the drawer (this closes the "blank space" half of the report — the space was invisible mail + button, both real elements).

### Verification (rendered DOM + real browser + real server, no restart needed)

- **r7qa.mjs (new): 42/42, zero console errors** — Workspace geometry at 1181/1280/1440 (`gap 0`, below trigger, in viewport, 328 px), real-mouse hover open, pointer travel into panel keeps it open, Escape closes, outside click closes, keyboard Enter opens; drawer computed colours at 1068/1024/390 (teal/dark on white; identity visible; expected link list incl. Workspace tools); drawer closes on link click; Specialities + Doctors megas still open (1128 px, in viewport); pairwise overlap oracle for doctor/patient/anon at 1181/1280/1440 with **zero intersecting pairs**.
- **A regression caught and fixed during verification:** after the first contrast fix the screenshot showed the brand dark-on-photo at 1068 — the `.brand` restoration was reverted (see above), then re-verified: bar brand `rgb(255,255,255)` over the photo, drawer still readable, anonymous bar at 1068 untouched (white links, no toggle, bar mode).
- **navfixqa.mjs re-run on the final CSS: 335/335** — all Revision 6 guarantees hold at 14 widths (the run also flags a probe-harness matter: the QA admin user must exist; it was recreated for the runs and deleted again below).
- **Regression surface:** `liveqa` 37/37, `navqa` 27/27 (no console errors); `manage.py check` 0 issues; `makemigrations --check --dry-run` no changes; full pytest **228 tests OK (1 skipped, 329 s)**; `git diff --check` clean (CRLF advisories only); `git status --porcelain` 78 lines — no files added; braces balance 592/592.

### Screenshots (inspected while iterating: C:\Users\Ramprasad\AppData\Local\Temp\opencode\phase-navdoc\shots\)

Before evidence: `r7_before_ws_1440.png`, `r7_before_drawer_1068.png` (blank white drawer as reported), `r7_before_drawer_390.png`. After: `r7_ws_1440.png`, `r7_ws_1280.png` (panel under the trigger), `r7_drawer_1068.png` (fully readable drawer incl. identity + Log out), `r7_drawer_390.png`, `r7_mega_specialities_1440.png`, `r7_mega_doctors_1440.png`.

### Changed trade-offs (flagged for human review)

- The Workspace panel is now trigger-aligned instead of container-right-aligned — the only visual change on the desktop bar is where the panel appears; its opening behaviour (hover or click), contents and keyboard accessibility are unchanged.
- The authenticated drawer at 901–1180 now shows the identity block (email/role) again; desktop teal/white hero styling for the anonymous bar is untouched.
- The QA harness `navfixqa.mjs` logs if the `qa-nav-*` users are absent (they are ephemeral by design; this revision recreated doctor+admin+patient in-session and deleted them again).

_Environment note: verified on the live dev server (PID 28656) on 127.0.0.1:8000 throughout; no server restart was needed._
