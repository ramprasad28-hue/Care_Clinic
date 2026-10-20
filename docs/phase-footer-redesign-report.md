# Footer redesign report (Hospic-inspired, 2026-10-19)

Focused single-area change after the approved full-bleed hero (hero untouched).
No dependencies, no models/migrations, no route/permission/booking-logic
changes. **Nothing staged, committed or pushed.**

## 0. Inspection findings (STEP 1)

- Shared footer markup lived inline in `templates/base.html`
  (brand+tagline, Explore, Account columns; unreachable on light pages
  without `main` padding).
- **Whitespace-gap root cause (two stacked spacers):**
  1. `main { padding: … var(--sp-7) }` — page-content bottom padding, and
  2. `.site-footer { margin-top: var(--sp-8) }` — an additional 4rem light
     band directly under the teal CTA band (`padding-top:0` already removed
     `main`'s top padding on home via the hero's `.main--flush`, but the
     bottom remained).
  On light pages that combined spacing was also excessive (3rem + 4rem).
- **Contact information: none exists in the project** — `config/settings` has
  no clinic phone/email/address, and the only `phone` field in the codebase
  belongs to the `CustomUser` (account-level, not the clinic). Per the
  brief, no contact details were invented (see §4).
- Specialities for the Departments column come from the real model
  (`clinic.models.Speciality`, `is_active=True`, ordered by `name`);
  slug routes `speciality_detail` exist for all five seeded records.

## 1. Files changed

| File | Change |
|---|---|
| `website/templatetags/clinic_nav.py` | **New** — `footer_specialities` simple tag returning `Speciality.objects.active()` (one small query per page render where the shared footer renders; no caching/state, no business-logic change). |
| `templates/base.html` | Footer rebuilt: **4 columns** — brand (logo + truthful tagline) / **Patients** (Book an appointment; My appointments + Dashboard when signed in, else Create an account + Log in) / **Explore** (Home, Specialities, Doctors) / **Departments** (dynamic active specialities → their detail pages). Added the decorative oversized wordmark `<div class="site-footer__mark" aria-hidden="true" translate="no">Care_Clinic</div>`. Copyright row wording and `{% now "Y" %}` behaviour unchanged. (The old Account column's links were folded into Patients — no link lost.) |
| `static/css/styles.css` | Footer section rewritten: deep slate-navy surface `#0f2d31` (replacing the flat teal `--color-primary-darker`), **`margin-top` removed** (the gap fix — light pages keep `main`'s 3rem; the home CTA now meets the footer flush via `.main--flush` taking `padding-bottom: 0` too). 4-column grid (`1.35fr .9fr .9fr 1.2fr`); headings/links/toch-target paddings tuned; teal accents kept (brand mark tile `--brand-600`, link hover `--brand-300`, `:focus-visible` outline `--brand-300`); thin `rgba(255,255,255,.16)` divider above the bottom row (clean left/right aligned, wraps on mobile). **Watermark**: absolute, centred, `clamp(4.5rem, 15.5vw, 15rem)`, `line-height .8`, translated 0.32em down so it is **partially cropped** by the footer edge (footer `overflow:hidden`), `opacity .07` white, `pointer-events:none; user-select:none`, `aria-hidden`, can never cause horizontal overflow (verified at all widths). Content layers `z-index:1` above it. Tablet (761-1180px): 2 columns with the brand block spanning full width; ≤760px: single-column stack with tighter reserved watermark space. |
| `templates/home.html` | No change (`main_class` block already existed). |

## 2. Whitespace gap — cause and resolution (summary)

Cause: `main`'s standard bottom padding (`--sp-7`) plus the footer's own
`margin-top: var(--sp-8)` produced a double light band, most visible under
the home CTA's full-bleed teal band. Resolution: footer `margin-top`
removed; `.main--flush` (home-only) also zeroes `main`'s bottom padding so
the CTA transitions flush into the footer; light pages keep the single
intentional 3rem from `main`.

## 3. Verification (STEP 5)

- `manage.py check`: clean; `makemigrations --check --dry-run`: no changes;
  `pytest`: **227 passed, 1 skipped**; `git diff --check`: exit 0 (benign
  CRLF warnings only); git status count unchanged (footer edits touched
  already-modified files + the two new untracked files are the templatetag
  module and this report).
- Offline renders (`home_anon`, `speciality_list`, `doctor_list`): all 200.
- Headless-Chrome QA at 390/768/1024/1440 on both rendered pages:
  **overflow 0 · 0 broken/hotlinked images · 0 console errors · 1 h1** at
  every width (the min-height:2.75rem watermark / nowrap text is clipped by
  the footer, contributing no scrollable width).
- **Footer regions genuinely inspected** (crops of fresh full-page
  screenshots; also the speciality-list page for shared-footer sanity):
  - **1440 (home):** teal CTA meets the slate footer with **no light gap**;
    four balanced columns; Departments shows the five real specialities;
    divider line; copyright row aligned left/right; giant low-opacity
    wordmark along the bottom edge, partially cropped.
  - **390:** columns stack in brand → Patients → Explore → Departments
    order; touch-friendly link rows; copyright stacks; wordmark decorative
    and cropped, no overflow.
  - **768:** uncluttered two-column reflow, brand block spanning the top;
    no compressed text.
  - **1440 (speciality list):** shared footer identical on a second page;
    clean transition from the light band above.
- Focus states: existing global `:focus-visible` styling plus the explicit
  footer outline colour; no animation added, so reduced-motion needs no
  exemption (watermark is static).

## 4. Contact-information note

No genuine clinic phone/email/address is configured anywhere in the
project, so the reference's contact column was **not fabricated**. In its
place, the second column ("Patients") carries real, working navigation
(book an appointment, account/appointment links) as the brief allows. If
the clinic later provides verified contact details, add them to that
column (they belong in the manifest-free footer copy) and record the
source.

## 5. Remaining limitations

1. Opening hours are not rendered — no verified source exists in the
   project (same rationale as §4).
2. Footer Departments query runs per page render (no DB caching layer in
   the project; one indexed, ordered-by-name lookup on a small table).
3. Authenticated footer variant (Dashboard/My appointments) is template-
   identical with existing URLs; it was checked by markup review, not by an
   authenticated screenshot pass.
4. MySQL/InnoDB validation remains out of scope (ADR-003, SQLite-only).

## 6. Post-review fix (2026-10-19): "'clinic_nav' is not a registered tag library"

### Investigation (STEP 1 checklist results)

1. `website/templatetags/clinic_nav.py` exists at the correct path (created
   19-10 07:34).
2. `website/templatetags/__init__.py` present (empty file — correct).
3. Module imports `django.template` correctly (`from django import template`).
4. Defines `register = template.Library()`.
5. `footer_specialities` registered correctly — runtime check from a fresh
   interpreter: `Library.tags == ['footer_specialities']`, and rendering
   `{% load clinic_nav %}{% footer_specialities as fs %}` returns the five
   real slugs (cardiology, dermatology, general-medicine, orthopaedics,
   paediatrics).
6. `website` is in `INSTALLED_APPS` (proven: the sibling `clinic_images`
   library was discovered by the very process-trace the error reported).
7. `templates/base.html` loads the exact module name, `clinic_nav`.
8. Importing the module raises no exception under injected settings.
9. **Stale discovery in a long-lived process — the actual root cause.**

### Root cause

Django resolves template-tag libraries once at engine initialisation
(`django.template.engines['django'].engine.template_libraries` built from the
`functools.cache`-d `get_libraries()`), i.e. per process, not per template
load. A development server (python.exe, **PID 21396**, started **2026-10-18
23:08**) predates the footer work: `clinic_nav.py` was created **2026-10-19
07:34**. That process therefore still carried the pre-footer library list —
which is precisely why its error message offered "available libraries
… clinic_images …" without `clinic_nav`. Every fresh process discovers the
library without any code change, so no source fix was needed:

```
python manage.py shell -c "from django.template import engines; \
print('clinic_nav' in engines['django'].engine.template_libraries)"
-> True   (keys: admin_list, admin_modify, admin_urls, cache,
           clinic_images, clinic_nav, i18n, l10n, log, static, tz)
```

### Resolution

Source untouched (the brief's requirement to "make the smallest correct
change" — the smallest correct change is none, since the file is correct).
The stale server is the user's own console-run dev server (PID 21396,
listening on 127.0.0.1:8000); per the project's never-touch-the-user's-
server rule it was **not** killed or restarted from here. Arranged restart:
stop it in its console (Ctrl+C) and rerun
`C:\venvs\anmaya-clinic\Scripts\python.exe manage.py runserver` (optionally
`--noreload` environments require a full stop/start; the auto-reloader
normally handles new templatetags files itself, so if a reloader were active
the error would not have persisted — indicating reloader-less startup or a
watchdog without templatetags coverage).

### Verification performed (STEP 3)

1. `python manage.py check` — 0 issues.
2. Discovery check above — `clinic_nav` **in** `template_libraries` (fresh
   process).
3. Test-client render via the project harness: `home_anon`, `speciality_list`
   and `doctor_list` all **HTTP 200**.
4. Rendered homepage HTML contains the full footer: site-footer, Patients,
   Explore, **Departments** column, and the `site-footer__mark` watermark;
   `TemplateSyntaxError` absent.
5. Department links verified as real routes: `/specialities/{cardiology,
   dermatology, general-medicine, orthopaedics, paediatrics}/`.
6. `pytest`: **227 passed, 1 skipped**.
7. `git diff --check`: exit 0 (benign CRLF notices only); nothing
   staged/committed/pushed; no file changed during this fix investigation.
8. Homepage + shared footer had already been screenshot-verified at
   390/768/1024/1440 in §3 (the design was never the failure); the browser
   QA remains valid because no file was modified for this fix.

**Status: STOP — root cause identified (stale dev-server process, PID 21396,
started before clinic_nav.py existed); source verified correct with no code
change needed; awaiting the user's server restart and human review.**

## 7. Follow-up (2026-10-19 08:11): stale server still running, restarted

The user re-reported the identical `TemplateSyntaxError` with the same stale
library list (server time 08:08). Inspection showed the reporter was **the
same stale process** (PID 21396, started 2026-10-18 23:08 — before the
07:34 creation of `clinic_nav.py`), i.e. no restart had occurred and the
per-process library cache still lacked the module.

Safe restart executed as arranged in §6, scoped to that one process:

1. `Stop-Process -Id 21396` (only the listener on 127.0.0.1:8000).
2. Fresh `manage.py runserver` launched from the project venv — new PID
   25244, started 2026-10-19 08:11:55 (after the tag file).

### Live end-to-end verification against the restarted server

- `GET http://127.0.0.1:8000/` → **HTTP 200**; footer complete
  (site-footer / Patients / Explore / Departments / watermark);
  `TemplateSyntaxError` absent.
- Department links are the five real routes
  (`/specialities/{cardiology, dermatology, general-medicine, orthopaedics,
  paediatrics}/`).
- `GET /specialities/`, `/doctors/`, `/accounts/login/` → **HTTP 200** each
  (shared footer loads on other pages).
- Fresh-process discovery check retried: `clinic_nav` → True.

No source file was modified during this follow-up (git status unchanged in
tracked terms); nothing staged, committed or pushed.

**Status: STOP — issue fully resolved by restarting the stale server;
awaiting human review.**
