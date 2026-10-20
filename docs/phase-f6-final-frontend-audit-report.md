# Phase F6 — Full Frontend QA & Final Audit Report

**Date:** 2026-10-20
**Scope:** Whole-app frontend quality audit after F1–F5: live-functionality probes, consistency / responsiveness / accessibility checks, automated gates, targeted frontend defect fixes, and screenshot review. This phase fixes genuine frontend (or frontend-reachable) defects only; deeper backend semantics (auth redirects for logged-in users, dashboard scope definitions) are deferred to **B0+**, and imagery management to **C1**, per the roadmap.

Surfaces covered: all page families at 1440 px and 390 px — public (home, specialities, doctors, auth), patient booking flows, doctor self-service, receptionist operations, admin dashboards, plus reduced-motion and JS-disabled modes.

---

## 1. Defects found and fixed

| # | Defect | File | Fix | Verification |
|---|---|---|---|---|
| 1 | Mojibake: `â€™`/`â€”` sequences in 4 `app.js` comments (UTF-8 read through CP1252) | `static/js/app.js` | Rewrote the 4 comments as plain ASCII findings notes | Served JS re-checked byte-clean |
| 2 | Duplicate `.hero > .container` rule (second occurrence silently masked the first) | `static/css/styles.css` | Removed the duplicate block | `grep -c ".hero > .container"` → single hit; braces balanced |
| 3 | **No success feedback** after doctor self-service create/update of availability rules and leaves | `clinic/views.py` | Added `SuccessMessageMixin` (`from django.contrib.messages.views import SuccessMessageMixin`) to `AvailabilityCreateView` ("Availability rule was added."), `AvailabilityUpdateView` ("Availability rule was updated."), `LeaveCreateView` ("Leave was added.") | UI probe: POST now lands with a visible flash message on `/clinic/availability/` |
| 4 | **HTTP 500 on duplicate availability rule**: the overlap `ValidationError` raised inside `instance.save()` because the doctor was bound to the form instance only *after* form validation | `clinic/views.py` | `get_form()` override on `AvailabilityCreateView`/`AvailabilityUpdateView` attaching `form.instance.doctor = self.get_doctor()` before validation | Repro POST then returned the rendered form with the inline error "This window overlaps an existing availability rule for this doctor." (status 500 → 200); duplicate rules blocked at DB (basis: rules 19/20 got `end_time → date + 1h` bumps during probing, `__str__`) |
| 5 | Unbound filter form visually defaulted to "Requested" while the receptionist list showed all statuses | `dashboards/forms.py` | `AppointmentFilterForm.status.choices` now starts with `("", "All statuses")` | GET default select value `""`; recaptured `f6_receptionist_dash_1440.png` |

> Notes: #3–#5 sit on the backend file but are strictly frontend-reachable UX defects (missing feedback, a 500 caused by form/data wiring, a misleading form default). No models, migrations, permissions, URLs, or workflows changed. Probe-driving fixes (wait loops, etc.) are in the QA harness only, not the app.

## 1b. Sign-off correction — Upcoming must exclude cancelled appointments

**Issue raised at review:** the patient dashboard's "Upcoming" section included CANCELLED appointments (the heap was date-scoped only), which read as misleading even though the status badges were honest.

**Fix (smallest correct change, using the application's existing status rules):**

| File | Change |
|---|---|
| `dashboards/views.py` — `PatientDashboardView.get_context_data` | `upcoming` queryset now chains `.active()` — the pre-existing `AppointmentQuerySet.active()` (`appointments/models.py:165`), which filters `status__in=ACTIVE_STATUSES` (`REQUESTED`, `CONFIRMED`, `CHECKED_IN`). No new status values, no model/service/permission/URL changes |
| `dashboards/tests.py` — `PatientDashboardTests` | Two regression tests: `test_upcoming_excludes_cancelled_appointments` (future CANCELLED appointment absent from `upcoming` context + not in rendered HTML by reference; future CONFIRMED appointment still present) and `test_cancelled_future_still_available_on_list` (the same cancelled appointment is still rendered on the general `/appointments/` list) |
| `dashboards/templates/dashboards/patient_dashboard.html` | One copy fix in the "Past appointments" empty state: *"Completed and cancelled **past** visits are kept here as a record; see 'All my appointments' for the full list."* — the old wording implied cancelled visits of any date are kept in the Past section, which is exactly the mislead being corrected (future-date cancelled visits live only on the list). No test asserted the old sentence |

**Verification (actual results):**

| Gate | Result |
|---|---|
| `manage.py test dashboards appointments` | Ran 124 tests, **OK (skipped=1)** |
| `manage.py test` (full suite, re-run after ALL correction edits incl. template copy) | **Ran 230 tests, OK (skipped=1)** (expected negative-case `Forbidden` log lines only) |
| `manage.py check` | 0 issues |
| `manage.py makemigrations --check --dry-run` | "No changes detected" |
| `git diff --check` | clean (CRLF warnings only) |
| Live UI check (rebuilt server, temp demo patient) | Dashboard Upcoming shows only the future CONFIRMED appointment (`CC-2026-000058`); the future CANCELLED one (`CC-2026-000059`) is excluded; `scrollWidth == innerWidth` (overflow 0) at both widths; the same cancelled reference IS present on `/appointments/` list |

**Screenshots inspected** (`%TEMP%\opencode\phase-f6\shots\`, temp demo data seed → cleanup afterwards):
- `f6c_patient_dash_1440.png` — Upcoming table lists only `CC-2026-000058 Fri 23 Oct 2026 · Confirmed`; corrected empty-state copy rendered
- `f6c_patient_dash_390.png` — same state at mobile width, single stacked-card row, no overflow
- `f6c_appt_list_1440.png` — "All my appointments" shows BOTH rows incl. the cancelled one → historical/cancelled access preserved

**Temp demo data** (`f6c-patient@example.com` + 2 appointments + 2 slots) was deleted after capture; rebuilt DB re-verified at the documented baseline: 540 slots (536 OPEN), 1 appointment, 0 correction artifacts.

**Known same-shaped behaviour (left as-is, out of this correction's scope):** the doctor dashboard's date-based "Today/Upcoming/Past" heap and the receptionist/admin date scopes are operational views that display full status columns and management actions (cancelled rows offer no actions, `_ACTION_EXCLUDED = {CANCELLED}`). If a similar exclusion is wanted there, that is a B0+ decision.

## 2. Non-defects investigated (documented, intentionally not changed)

These behaviours look odd at first glance but are correct or out of frontend scope:

| Finding | Verdict |
|---|---|
| ~~Patient dashboard "Upcoming" section also lists CANCELLED appointments~~ — **fixed on sign-off correction** (see section 1b); the general "All my appointments" list (date-based scopes, no status filter) keeps cancelled appointments accessible | Corrected |
| Same-slot rule: rescheduling to the current slot returns "The appointment is already on that slot." | **Correct** validation message |
| Specialities card count 5 → 7 vs pre-F2 expectations | **Data**, not UI: user created 2 live specialities → left intact (probe expectations corrected, not the app) |
| Register flow: probe/seed harnesses create `qa6-*` accounts; removed cleanly in the F6 cleanup (below) | Harness-side only |
| Registration e-mail conflicts render as in-card field errors, not page-level alerts | Standard Django `AuthenticationForm`/form rendering; acceptable |
| Wrong booking URL `/doctors/dr-aswin-kumar/book/` → Django DEBUG 404 | URL is `/appointments/book/aswin-kumar/`; debug 404 is DEBUG-mode only |
| Garbled single-character drops seen in captured debug pages (`' tart_time'` for `'start_time'`) | **Capture artifact** of the CDP/PowerShell read path, NOT app bytes — raw HTTP responses verified clean |

## 3. Live probe suites (results)

All suites ran against the live dev server (SQLite database seeded by the F6 seed script) at 1440×900 / 390×844 viewports:

| Suite | Result |
|---|---|
| `qa6-nav.mjs` (global navigation correctness) | **20/20 PASS** |
| `qa6-app.mjs` (whole-app functional probes) | **93/93 PASS** (23 page visits) |
| liveqa (`liveqa.mjs`, re-run **after** all F6 fixes) | **37/37** |
| navqa (`navqa.mjs`) | **27/27** |

`qa6-app.mjs` coverage highlights — per-role end-to-end flows:

- **Global nav** on every visit: header/nav/identity/chips render, mega `aria-expanded` toggles open/shut, Escape and outside-click close the panel, mobile drawer works, no horizontal overflow (`scrollWidth == innerWidth`).
- **Patient**: log in (real form), identity shows email, book (date chips + slot radio + confirm → CONFIRMED on patient dash), duplicate attempt surfaces the validation message instead of a 500, reschedule (`2026-10-23`, different slot) + confirm, cancel via UI (CONFIRMED → CANCELLED, slot freed), patient dash card counts + status badges.
- **Doctor**: login `qa6-doctor@example.com / QA6-pass-99!` → dash (identity + avatar + speciality + "Accepting appointments" pill), workspace open (form + table row), availability add (new window from the form's own `start_time`) + flash "Availability rule was added.", availability edit (+1 h) + flash "…was updated.", duplicate add → inline overlap error (no 500), delete via UI → row gone + slot count drop, leave add → "Leave was added.".
- **Receptionist**: "Book for a patient" (patient filter → date chip → slot → book → REQUESTED reference), status Confirm action → CONFIRMED (badge updates), pagination (`?page=2` renders the right slice).
- **Admin**: login `qa6-admin@example.com / QA6-admin-99!` → dash → stat cards and the status breakdown at real counts.
- **Auth**: wrong-password inline error, register (all form fields → auto-login → qa6 account), password-reset done page + invalid reset token page.
- **Reduced-motion**: mega menu still opens, reveals visible immediately.
- **JS-disabled**: `html.no-js`, reveals visible, plain speciality link replaces trigger, no overflow, doctor filter select + submit button usable.

## 4. Automated gates

```text
manage.py check           → 0 issues
makemigrations --check --dry-run        → "No changes detected"
manage.py test            → 228 tests, OK (skipped=1), ~229 s (sqlite)
git diff --check          → clean (CRLF warnings only)
```

*(Prior scratch note — pytest is not configured for this project; the Django test suite is the project's test runner as in F1–F5.)*

## 5. Screenshot review (Step 9)

Screenshots captured at 1440×900 and 390×844 under
`%TEMP%\opencode\phase-f6\shots\` (filename suffixes `…__1440.png` / `…__390.png`) were each opened and reviewed. All clean:

- **Layout**: no clipping/overflow; `scrollWidth` == innerWidth on all audited pages; dashboards and home coherent both widths; card/action grids collapse cleanly; drawer works at 390.
- **Type/mojibake**: all visible strings clean (both templates and probe-rendered content); speciality names, statuses, dashboards, forms render readable en/em-dashes and apostrophes.
- **Forms**: invalid login renders in-card field errors (screenshot `f6_login_invalid.png`); booking form pickers (date chips + slot radio) intact; register form has all fields (first_name, last_name, email, phone, password1, password2); filter form default "All statuses".
- **Images/avatars**: `doctor_avatar`/`doctor_portrait` initials fallbacks render; `full-width-art`/`_art` blocks intact on doctors/specialities/home.
- **Files reviewed (26)**: `f6_home` {1440,390}, `f6_specialities__` {1440,390}, `f6_doctors__` {1440,390}, `f6_mega_specialities_1440`, `f6_mega_doctors_1440`, `f6_patient_dash_1440/390`, `f6_appt_list_1440/390`, `f6_appt_detail_1440/390`, `f6_booking_1440/390`, `f6_booking_invalid`, `f6_booked_detail`, `f6_doctor_dash_1440`, `f6_workspace_open_1440`, `f6_availability_1440`, `f6_receptionist_dash_1440`, `f6_admin_dash_1440`, `f6_login_invalid`, `f6_accounts_register__390`, `f6_accounts_login__390`.

## 6. Data state (cleanup + known drift)

F6 cleanup (transactional, verified) removed ALL QA6 probe data:

- Deleted: **32 probe appointments** (the 3 seeded `QA6-*` + 29 probe-created `CC-2026-*` booked by QA6 patients) with their **15 slots reopened to OPEN**; **5 qa6 users** (patient / empty-patient / receptionist / administrator / doctor — cascading the doctor's `Doctor` profile, remaining availability rules and leaves); **14 qa6 leave records**; plus the once-registered `qa6-register@example.com` account (created by the register-flow probe, verified working, then deleted).
- Preserved exactly: `admin@care.com`, the 3 durable doctors (`dr.aswin` / `dr.meera` / `dr.rahul`, 180 slots each) + the seeded `Dr. ram@care.com` doctor profile, **7 active specialities** (including the user-created `pulmonologists` + `rep`), the 1 real appointment `CC-2026-000004` (patient `saravananramprasad776@gmail.com`), groups and all F1–F5 content.
- Final counts: **0 `qa6-` users, 0 `QA6-*`/probe `CC-*` appointments, 6 users, 4 doctors, 7 specialities, 540 slots (536 OPEN), 1 appointment**, and home renders `200` with the correct fresh data.

## 7. Environment & harness notes

- All probes/gates ran with `DB_ENGINE='sqlite'` and create-test-data applied via the F6 seed; the dev server (`C:\venvs\anmaya-clinic\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload`) was restarted between code-fix batches so every probe hit the fixed code (server restarted after the last fix before the final 93/93 run and the screenshot batches).
- QA harnesses (qa6-nav.mjs, qa6-app.mjs, seed/cleanup/debug scripts, screenshots) live in `%TEMP%\opencode\phase-f6\` by design — outside the repository, like all previous phase harnesses.
- Logout UX invariant confirmed again: `templates/base.html` renders the logout form as the page's first `<form>` element — harness selectors always scope to the specific form containing the target fields (lesson recorded for future QA; no user-facing defect).

## 8. Git preservation

- `git status --porcelain` start-of-F6: **81 entries**; at report time: **85** (`clinic/views.py`, `dashboards/forms.py`, `dashboards/views.py`, `dashboards/tests.py`, `dashboards/templates/dashboards/patient_dashboard.html` changed for the F6 fixes + sign-off correction; nothing staged/committed, nothing lost).
- All F6 code artifacts live in-place in the working tree: `static/js/app.js` (untracked, created in the frontend phases), `static/css/styles.css`, `clinic/views.py`, `dashboards/forms.py`, `dashboards/views.py`, `dashboards/tests.py`, `patient_dashboard.html`, plus the docs/reports.
- The harness (mjs/py probes, shots) stays in `%TEMP%\opencode\phase-f6\` by design (outside the repo).

## 9. F6 sign-off checklist

| # | Item | Status |
|---|---|---|
| 1 | All F1–F5 surfaces mentioned and the navbar report's open points closed | ✅ |
| 2 | Whole-app probes 20/20 + 93/93 (liveqa 37/37 + navqa 27/27) with all fixes in place | ✅ |
| 3 | Django suite 228 OK at audit time; **230 OK after sign-off correction** / check clean / makemigrations check clean / `git diff --check` clean | ✅ |
| 4 | 26 screenshots reviewed at both widths during the audit; **+3 correction screenshots inspected** (`f6c_patient_dash_1440/390`, `f6c_appt_list_1440`) | ✅ |
| 5 | Data cleaned to the documented baseline (0 qa6-/f6c-, preserves user-created data) | ✅ |
| 6 | Sign-off correction (Upcoming excludes cancelled; regression tests + gates) delivered | ✅ |
| 7 | **Awaiting user review of this report** before F6 is closed and C1 begins | ⬜ |
