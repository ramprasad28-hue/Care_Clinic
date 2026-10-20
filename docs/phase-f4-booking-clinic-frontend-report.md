# Phase F4 — Booking, Appointment Management & Clinic Workflow Frontend Redesign Report

**Date:** 2026-10-20
**Scope decision:** Phase 7.5 already applied the premium editorial design language to booking/management/clinic pages (page-head, breadcrumb, date-chip, slot-grid, ticket, badge, confirm components). F4 therefore focused on targeted upgrades and gap-filling on those pages rather than rewriting working markup — preserving every field id/name, action, redirect, and status transition.

## Surfaces covered

| Direction | Pages touched |
|---|---|
| Appointment booking | `doctor booking` (choose date/time), `receptionist book-for-patient` (`/dashboard/receptionist/book/`) |
| Appointment management | `appointments list`, `appointments detail`, `appointments cancel`, `appointments reschedule` |
| Doctor availability & leave | `availability list/form`, `leave list/form`, both delete-confirm pages |

## Key changes

### Booking (`appointment_book.html`, `appointment_reschedule.html`)
- New doctor identity strip at the top (portrait via the existing `doctor_portrait` template tag, name, speciality PIL badge, "View profile" link) so the page names who is being booked.
- `booking-summary` card echoes the current selection (patient/doctor/date via form field, **live time** kept in sync by a small JS addition when a slot radio is checked).
- Contextual empty states per scope (no rules at all vs. inactive-only vs. fully booked day).
- Reschedule page reuses the same strip plus a "current slot" context line.

### Appointment management
- `appointment_detail.html`: the ticket card now opens with a `ticket__person` row (avatar/portrait + doctor name + speciality pill + patient line), reusing the existing ticket stub styling.
- `appointment_list.html`: scope-aware empty states for "no bookings / nothing upcoming / only past" instead of the single muted sentence.
- `appointment_cancel.html`: a `cancel-summary` definition list (doctor, date, time, reference) plus a static `confirm-note` explaining that the slot is released back to open availability (verified against `services.py:215` cancel/release behaviour).

### Clinic workflow (`availability_list.html`, `leave_list.html`, forms, confirm deletes)
- Active/Inactive state pills (`badge status-confirmed` / `status-no_show`) — state carried by label + dot, never colour alone.
- Availability rules listed as readable `day-cell` blocks with slot length; footnote explaining inactive rules generate no slots.
- Delete-confirm pages use the existing `confirm` component; forms kept untouched functionally apart from the save-button label ("Save availability rule" / "Save leave").

### Receptionist booking (`receptionist_book.html`)
- Added the same `booking-summary` card (patient, doctor, date) with a `% if selected_patient %` guard; live slot-time sync via the same JS hook.

### CSS (`static/css/styles.css`, appended F4 component block)
- `.booking-doctor*`, `.booking-summary*`, `.cancel-summary`, `.confirm-note`, `.table-footnote`, `.day-cell`, `.ticket__person*`, polished native `select/input[type=time|date]/checkbox`, and ≤768 stacking rules. Braces balanced (635/635).

### JS (`static/js/app.js`)
- New standalone IIFE: `form[data-slot-form]` syncs `[data-slot-summary-time]` from the checked slot radio's `.slot-time` text on `change` + `pageshow`; "Not selected yet" fallback otherwise.

## Functionality preservation — verified through the real UI (Chrome DevTools Protocol, unmodified app)
A workflow probe drove the actual pages at 1440/390 through all critical flows. **25/25 checks passed:**
- Patient login → live summary syncs on radio change → successful booking POST → redirect to `/appointments/<reference>/` → success message.
- Reschedule via UI (re-pick slot) → redirect + "Appointment rescheduled."
- Submitting without a slot → validation error "Please choose an available slot." rendered on the booking page (screenshot: `w_book_validation_error`).
- Cancel via UI → "was cancelled" message → `status-cancelled` badge on detail.
- Doctor availability: add (list grows), edit save → back on list, delete confirm page → row count returns. Caveat below.
- Doctor leave: add/delete round-trip.
- Receptionist books for a patient (summary shows patient name/email + date) → success message "Booked CC-… for <patient>", then cancelled afterwards to restore state.
- Radio inputs keyboard-focusable; no horizontal overflow at 390; **zero console errors across all workflows.**
- Note: during probing, a first attempt to add an availability window was correctly **rejected by the overlap validator** (`clinic_avail_unique_window` / `clean()`) — the UI shows the inline field error; this is intended behaviour, exercised incidentally.

## Gates
- `manage.py test` — **228 tests, OK (1 skipped)** — full suite rerun after every template touch.
- `manage.py check` — clean. `makemigrations --check --dry-run` — no changes detected. `git diff --check` — clean (only pre-existing CRLF warnings).
- `navqa` regression suite — 27/27. `liveqa` — 35/37 (see limitations).
- Screenshots (37) in `C:\Users\Ramprasad\AppData\Local\Temp\opencode\phase-f4\shots\`: booking default/slots/390, detail/cancel/list/reschedule at 1440+390, availability & leave lists/forms/empty states, receptionist booking at 1440/390, plus workflow result captures.

## Test-fixture incidents (self-inflicted, resolved)
- Humanizing leave dates (`D j M Y`) broke `clinic/tests.py` which asserts the `Y-m-d` string; the test suite is the contract, so the date format was **reverted to `Y-m-d`** while keeping the improved table/stack markup.
- A probe typo (`/dashboards/receptionist/book/`) captured a 404 screenshot; recaptured with the correct `/dashboard/receptionist/book/`.

## Backend defects found separately (not fixed here — backend-polish phase)
- `clinic/views.py` emits **no Django messages at all** for availability/leave create/edit/delete (success or error). Booking/cancel views do. Recommended: `messages.success(...)` on the four CRUD outcomes; the client can then rely on the existing base.html message component.
- `clinic/models.py` `AvailabilityRule.__str__` contains a mangled em-dash escape (`�?"`) visible in Django admin; trivial cosmetic fix candidate.

## Maintainership notes / limitations
- `liveqa`'s two failures count speciality mega-menu entries: the DB now contains a 6th sample speciality ("pulmonologists", created 2026-10-19 23:40, before F4 work began). No F4 file touches the speciality nav; treat as test-data drift (the script expects 5 categories).
- Leave dates intentionally keep the `Y-m-d` display (test contract); humanized dates remain on appointment tables where no test asserts the format.
- QA accounts (`qa4-patient/qa4-doctor/qa4-receptionist@example.com`, pw `QA4-pass-99`) and all seeded availability/leave/appointment rows were **deleted** after verification; `qa-*` user count is 0 and the rest of the DB is untouched.

## Files changed in this phase
- `appointments/templates/appointments/`: `appointment_book.html`, `appointment_reschedule.html`, `appointment_detail.html`, `appointment_list.html`, `appointment_cancel.html`
- `clinic/templates/clinic/`: `availability_list.html`, `leave_list.html`, `availability_form.html` & `leave_form.html` (button labels only), confirm-delete pages (markup unchanged or minor)
- `dashboards/templates/dashboards/receptionist_book.html`
- `static/css/styles.css` (appended component block), `static/js/app.js` (appended summary-sync IIFE)
