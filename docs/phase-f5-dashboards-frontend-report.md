# Phase F5 — Role Dashboards Frontend Polish Report

**Date:** 2026-10-20
**Scope:** Presentation-layer-only polish of the four role dashboards (`patient`, `doctor`, `receptionist`, `administrator`), following the F4/F2 editorial direction. Templates + CSS only — no changes to models, views, services, permissions, URLs, forms, field names, redirects or dependencies. `dashboards/views.py` was read as a reference for available context only.

## Surfaces covered

| Direction | Pages touched |
|---|---|
| Patient dashboard | `dashboards/templates/dashboards/patient_dashboard.html` |
| Doctor dashboard | `dashboards/templates/dashboards/doctor_dashboard.html` |
| Receptionist dashboard | `dashboards/templates/dashboards/receptionist_dashboard.html` |
| Administrator dashboard | `dashboards/templates/dashboards/admin_dashboard.html` |
| Shared table partial | `dashboards/templates/dashboards/_appointment_table.html` |
| CSS | `static/css/styles.css` (appended "Phase F5 — dashboard polish" block) |

## Key changes

### Shared `_appointment_table.html`
- New include flags **`hide_doctor` / `hide_patient`** (opt-in column suppression). Why *hide* flags and not *show* flags: inside the include, unset `{% if %}` variables are falsy, so `show_*` flags with a "default true" semantic cannot be expressed; default render (neither flag) still prints both columns exactly as before, so the existing include contract is unchanged.
- Richer empty state: optional `empty_title`, `empty_text`, `empty_action_url`, `empty_action_label` now render a proper `empty--inline` block (title + copy + CTA button) instead of the single muted sentence.
- Time cells keep the `HH:MM–HH:MM` en-dash format.

### Patient dashboard
- Editorial head (`section-rule` + eyebrow "Your visits" + personal greeting intro), primary "Book an appointment" CTA + secondary "All my appointments" link.
- Patient column hidden via `hide_patient=True`; per-section contextual empty states: upcoming empty state explains booking flow and links to the doctors list (`{% url 'doctor_list' as book_url %}`), past empty state explains the record-keeping purpose.

### Doctor dashboard
- Head with eyebrow "Your schedule" + intro distinguishing today/upcoming/past; identity strip below the intro: small `.dashboard__avatar` (portrait via existing `doctor_portrait` tag with initials fallback) + speciality pill + "Accepting appointments" pill + quick links ("My availability", "My leave", "All my appointments").
- Doctor column hidden via `hide_doctor=True`; `aria-labelledby` section ids (`today-heading`/`upcoming-heading`/`past-heading`) and status action buttons preserved.

### Receptionist dashboard
- Eyebrow "Front desk" + clinic-wide intro copy; a two-card **real-count stat strip** (`.dashboard__counts` reusing `stat-*` tokens) fed by the existing `today_count` / `upcoming_count` context.
- Added a "Today" quick link (`?scope=today`, applied and verified through the live filter form), "Book for a patient" primary CTA, "Browse doctors" secondary. All seven table columns (Reference, Date, Time, Doctor, Patient, Status, Actions) kept intact.

### Administrator dashboard
- Eyebrow "Clinic management" + intro separating catalogue/user management (Django Admin) from the on-surface appointment oversight; all stat cards kept (`stat-grid`/`stat-card`/`stat-value`/`stat-label` exact tokens); an explicit "Appointment operations" section now wraps the filter form + table + pagination; "Appointments by status" heading labelled the unchanged status breakdown.

### CSS (appended F5 block)
- `.dashboard__head` rule/eyebrow, `.dashboard__identity`, `.dashboard__avatar` (52px, `object-fit: cover`, initials fallback), `.stat-grid.dashboard__counts` sizing, `.empty--inline` heading/button styles, and ≤768 stacking adjustments. Braces balanced (648/648 checked).

## Encoding incident (found and fixed during review)
- The en/em dashes introduced into the F5 templates were written double-encoded (UTF-8 bytes re-read through CP1252 → literal "â€" text in the served HTML, e.g. `09:00â€“09:30`). Found by reading the rendered DOM (`codePointAt` probe) — not visible in code review.
- Fixed at byte/text level across the 5 touched templates; the whole `dashboards` template directory now decodes cleanly with zero mojibake characters. The running dev server had to be restarted (a stale `--noreload` process kept serving the pre-fix template), after which the live DOM serves proper U+2013/U+2014.

## Functionality preservation — verified through the real UI (Chrome DevTools Protocol, unmodified app)
Isolated QA accounts (`qa5-*`, seeded 5 users + 1 Doctor profile + 10 appointments) drove a 28-check browser session; **all 28 passed**:
- Each role dispatches to its correct dashboard; one single `<h1>` + `dashboard__head` block per page.
- Patient: patient column absent, doctor column present; reference link navigates to `/appointments/CC-...`; patient blocked from the doctor dashboard (403).
- Doctor: identity strip + pills render; own-schedule doctor column absent; three labelled sections; a status action ("Confirmed") executed through the real UI produced the expected Django success message; doctor blocked from the patient dashboard.
- Receptionist: two count cards with real numbers; filter form (`scope=today`) submitted through the UI; book CTA present.
- Administrator: ≥7 stat cards with real counts; operations section distinct from the stats; admin blocked from the receptionist and patient dashboards.
- No console errors across every checked page; no horizontal overflow at 390px for any role.
- Screenshots captured at 1440/1024/768/390 per role + patient empty states (`%TEMP%\opencode\phase-f5\shots2\`), reviewed visually — heads, stat strips, tables and empty states all consistent; dashes render correctly post-fix.

## Gates
| Gate | Result |
|---|---|
| `manage.py check` | 0 issues |
| `manage.py makemigrations --check --dry-run` | No changes detected |
| `manage.py test dashboards` | **54 tests OK** (after the hide-flag fix caught by an existing column assertion) |
| `manage.py test --parallel 1` (full suite) | **228 tests OK (1 skipped)** |
| `git diff --check` | clean (CRLF autocrlf warnings only, as in all prior phases) |
| navqa (`phase-img/navqa.mjs`) | **27/27** |
| liveqa (`phase-img/liveqa.mjs`) | **35/37** — the same 2 pre-existing sample-data drift failures documented in F4 (the sample specialities created 2026-10-19 23:40 break the "5 specialities" expectation; now `items=7`). Not F5 regressions. |
| CSS braces | 648/648 |

## Test incidents (self-inflicted, resolved)
1. **Include-flag inversion** — first version used default-on `show_*` flags, which broke the patient dashboard (doctor column duplicated patient column); test `<th scope="col">Doctor</th>` assertion caught it; converted to the opt-out `hide_*` design, all 54 dashboards tests pass.
2. **Double-encoded dashes** — see the dedicated section above.

## Backend defects found separately (not fixed here)
- Unchanged from F4: clinic views still emit **no Django messages** on availability/leave CRUD; mangled em-dash in `AvailabilityRule.__str__`. Out of scope for F5 (dashboard presentation only).

## Maintainership notes / limitations
- Dashboard `alt`/`aria` labels: portraits carry initials fallbacks; tables keep `role="region"` `aria-label="Appointments"` + `tabindex="0"` from F2 contracts; nothing new needs ARIA beyond section `aria-labelledby` (already tested).
- No new dependencies; no JS changes (the F4 slot-summary IIFE is untouched and not used on dashboards).
- QA5 accounts and their 10 appointments + Doctor profile were deleted at cleanup; `qa-*` user count is **0**.

## Files changed in this phase
- `dashboards/templates/dashboards/_appointment_table.html`
- `dashboards/templates/dashboards/patient_dashboard.html`
- `dashboards/templates/dashboards/doctor_dashboard.html`
- `dashboards/templates/dashboards/receptionist_dashboard.html`
- `dashboards/templates/dashboards/admin_dashboard.html`
- `static/css/styles.css` (F5 block appended)
- `docs/phase-f5-dashboards-frontend-report.md` (this file)

Git working tree: 80 porcelain entries (same as before F5 work started; nothing staged or committed).
