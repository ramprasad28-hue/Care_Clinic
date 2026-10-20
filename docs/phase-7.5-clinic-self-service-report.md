# Phase 9 — Clinic Self-Service Pages report

**Status:** complete — awaiting review. Nothing staged, committed, or pushed.

## 1. Scope
Phase 9 of the Phase 7.5 "premium editorial" restyle covers the doctor self-service surfaces in
`clinic/` — weekly **availability** and **leave** management — plus `static/css/styles.css`.

| Surface | Template | Route (name) | In scope | Covered |
|---|---|---|---|:--:|
| Availability list | `availability_list.html` | `clinic:availability_list` | yes | yes |
| Availability create | `availability_form.html` | `clinic:availability_add` | yes | yes |
| Availability edit | `availability_form.html` | `clinic:availability_edit` | yes | yes |
| Availability delete | `availability_confirm_delete.html` | `clinic:availability_delete` | yes | yes |
| Leave list | `leave_list.html` | `clinic:leave_list` | yes | yes |
| Leave create | `leave_form.html` | `clinic:leave_add` | yes | yes |
| Leave delete | `leave_confirm_delete.html` | `clinic:leave_delete` | yes | yes |

There is no leave *edit* route in `clinic/urls.py`, so no edit confirmation/form surface exists for
leave. Plan directives honoured: **Reuse** `.table-wrap` / `.data-table` / `.table-wrap--stack`,
`templates/partials/_field.html` and `_form_errors.html`, the `.row-actions` pattern and
`.empty.empty--inline`. **Refine** the tables and forms into the editorial grammar. **Replace:** none.
**Introduce:** none. `static/css/styles.css` required **no** edit (see §2.5).

---

## 1a. Files changed (Phase 9)

| File | Phase 9 change |
|---|---|
| `clinic/templates/clinic/availability_list.html` | `section-rule` lead-in above the `h1` in `.page-head`. |
| `clinic/templates/clinic/leave_list.html` | `section-rule` lead-in above the `h1` in `.page-head`. |
| `clinic/templates/clinic/availability_form.html` | `section-rule` lead-in above the `h1` inside `.auth-panel`. |
| `clinic/templates/clinic/leave_form.html` | `section-rule` lead-in above the `h1` inside `.auth-panel`. |
| `clinic/templates/clinic/availability_confirm_delete.html` | `aria-labelledby="delete-availability-heading"` on `.confirm` + matching `id` on the `h1`. |
| `clinic/templates/clinic/leave_confirm_delete.html` | `aria-labelledby="delete-leave-heading"` on `.confirm` + matching `id` on the `h1`. |
| `clinic/tests.py` | `ClinicTemplatePresentationTests` — three presentation-contract tests (see §5). |
| `docs/phase-7.5-clinic-self-service-report.md` | This report (new). |

**Context (important for review):** at inspection time the six clinic templates were *already*
modified versus `HEAD` with the bulk of the editorial restyle in place — `.container` /
`.container--form`, `.page-head`, `.table-wrap.table-wrap--stack` + `.data-table` with
`scope="col"` headers and `data-label` cells, `.row-actions` + `btn btn--ghost btn--sm`,
`.empty.empty--inline`, `.auth-panel`, `.form` + `novalidate`, `_form_errors.html` and per-field
`_field.html`, and `.confirm` + `.form-actions` with `btn--danger`. Phase 9 therefore **completed the
remaining consistency work** (page-head rule grammar; the confirm panel's accessible name) and
performed the full verification/documentation pass. `git diff` versus `HEAD` shows the whole restyle
for these six files; the Phase 9 additions are the `section-rule` spans and the
`aria-labelledby`/`id` pairs.

No shared partial was modified (Phase 3 owns `_field.html` / `_form_errors.html` / `_empty.html`), no
dashboard/booking template was touched, and no CSS was changed.

---

## 1b. Design direction applied

The clinic self-service screens now use the same **editorial page-head grammar** as the public, auth
and booking pages: a short teal rule (`<span class="section-rule" aria-hidden="true">`, 40 × 2 px,
`--brand-500` `#0EA5A8`) leads the display heading. The list pages place it in `.page-head`; the
create pages place it at the top of their `.auth-panel`, reusing the existing
`.auth-panel .section-rule { margin-bottom: var(--sp-3); }` rule. The confirm-delete pages
deliberately keep the single-purpose `.confirm` treatment (no rule — a destructive confirmation is not
a browsing section), matching the booking-cancel precedent, and now expose an explicit accessible name
via `aria-labelledby`.

The dense data tables keep their established `.data-table` styling (tabular-nums on numeric cells,
`.row-actions` for the per-row controls, and the `--shadow-sm` card surface shared with every other
instance panel). No new component or second design system was introduced.

---

## 2. Presentation changes (reuse, refine)

### 2.1 List pages (`availability_list.html`, `leave_list.html`)
- Added the `section-rule` above `h1` in `.page-head` (grammar parity).
- Tables already carried the required primitives and were verified, not rebuilt:
  `div.table-wrap.table-wrap--stack[tabindex="0"][role="region"][aria-label]` wrapping
  `table.data-table`, `thead th[scope="col"]` (availability 6, leave 4), `tbody td[data-label]`,
  `.num` on the availability time cells, `.row-actions` with `btn btn--ghost btn--sm` edit/delete
  controls, and the `.empty.empty--inline` empty state.

### 2.2 Create/override forms (`availability_form.html`, `leave_form.html`)
- Added the `section-rule` above `h1` inside `.auth-panel`.
- Forms already used `.container--form` → `section.auth-panel` → `h1` → `form.form[method=post][novalidate]`
  + `{% csrf_token %}` + `_form_errors.html` + `{% for field in form %}{% include "partials/_field.html" %}`
  + `.form-actions` (Save `btn--primary`, Cancel `btn--secondary`). Verified, unchanged.

### 2.3 Confirm-delete pages (`*_confirm_delete.html`)
- Added `aria-labelledby` on `.confirm` and a matching `id` on the `h1` so the confirmation panel has
  an explicit accessible name (parity with `appointment_cancel.html`).
- Structure already used `.container--form` → `section.confirm` → `h1` → `p` (object detail) →
  `form.form[method=post]` + `.form-actions` (Delete `btn--danger`, Cancel `btn--secondary`).

### 2.4 Confirmation copy
The delete prompts continue to render the object detail safely: availability shows the weekday +
`HH:MM`–`HH:MM` window, leave shows the `start_date`–`end_date` range. No user-supplied medical data
was added; no invented content was introduced.

### 2.5 CSS
No `static/css/styles.css` edit was necessary. Every primitive Phase 9 needed
(`.page-head .section-rule`, `.auth-panel .section-rule`, `.table-wrap`/`.table-wrap--stack`,
`.data-table`, `.row-actions`, `.empty--inline`, `.confirm`, `.form-actions`) already existed from
earlier phases. `.table-wrap`'s `box-shadow: var(--shadow-sm)` was intentionally left as-is — it is a
shared surface also used by the dashboards, and changing it would exceed Phase 9 scope.

---

## 3. Preserved backend contracts

Nothing below was touched (verified by diff — only the files in §1a changed):

- Models/schema: `Speciality`, `Doctor`, `AvailabilityRule`, `DoctorLeave` — including the DB
  `CheckConstraint`s (`clinic_rule_end_after_start`, leave `end_date >= start_date`) and the
  duplicate-window `UniqueConstraint`. **No migration was generated.**
- URL names and routes (`clinic:availability_list/add/edit/delete`, `clinic:leave_list/add/delete`).
- Views: `DoctorSelfServiceMixin(RoleRequiredMixin)` with `allowed_roles=(User.Role.DOCTOR,)`, and the
  querysets scoped to `doctor__user=request.user` (cross-doctor access still 404s).
- Forms `AvailabilityRuleForm` / `DoctorLeaveForm` — field set, `TimeInput`/`DateInput` `format`,
  `input_formats`, the `doctor`-field exclusion (forced by the view), and `Model.full_clean()`
  validation (end-before-start, overlap detection).
- The doctor/speciality workflows and appointment state/booking logic were not touched.

---

## 4. Accessibility & interaction checks

- **Table headers** — every `<th>` in both list tables carries `scope="col"` (6/6 availability,
  4/4 leave), so headers are programmatically associated with their cells.
- **Responsive/stacked tables** — at ≤ 640 px `.table-wrap--stack` hides thead (`position: absolute`,
  clipped) and stacks each row, with each cell exposing its label via `::before { content: attr(data-label) }`
  ("Day", "Start", …). Verified in the browser pass.
- **Region labelling** — the scrollable table region keeps `tabindex="0"`, `role="region"` and an
  `aria-label` ("Availability rules" / "Leave periods") so keyboard users can scroll it.
- **Labels & inputs** — every `label[for]` resolves to its control; `select` (weekday), `input[type=time]`
  (start/end), `input[type=number]` (slot length), `input[type=checkbox]` (active) and
  `input[type=date]` (leave start/end) render with correct native types.
- **Validation errors** — an invalid submit re-renders (HTTP 200) with `.field.field--error` wrapping
  a `.field__error` message ("End time must be later than start time." / "End date cannot be before
  start date."). Django 5.2 additionally emits `aria-invalid="true"` and
  `aria-describedby="id_<field>_error"` on the widget (see §8.2).
- **Confirmation semantics** — `.confirm` now has `aria-labelledby` resolving to the `h1` id.
- **Keyboard focus** — tabbing through the pages lands on every control with a visible 3 px solid
  `rgb(11,124,128)` outline (`--focus-color`), including the skip link, nav, the Add link, row-action
  buttons, all form fields, Save and the confirm Delete/Cancel actions.
- **Reduced motion** — with `prefers-reduced-motion: reduce`, control transition duration collapses to
  `1e-06s`; no motion-only affordance is used.
- **No-JS** — with scripting disabled the pages still render server-side: 6 scoped headers, 3 table
  rows and the `section-rule` are present; the tables/forms do not depend on `app.js`.

---

## 5. Regression tests added (`clinic/tests.py`)

| Test | Guards |
|---|---|
| `ClinicTemplatePresentationTests.test_tables_keep_scoped_headers` | both list tables render `scope="col"` headers. |
| `ClinicTemplatePresentationTests.test_list_and_form_pages_use_editorial_rule` | availability/leave list + add pages render the `section-rule` lead-in. |
| `ClinicTemplatePresentationTests.test_confirmation_panels_have_accessible_name` | both confirm-delete panels render the expected `aria-labelledby`. |

The plan's behavioural regressions already exist and were left intact:
`test_doctor_sees_only_own_rules` (asserts "Monday" present / "Tuesday" absent) and
`test_doctor_sees_only_own_leave` (asserts "2026-02-01" present / "2026-03-01" absent), plus the full
role/ownership-scoping suite.

---

## 6. Validation results

| Check | Command | Result |
|---|---|---|
| System check | `python manage.py check` | **No issues (0 silenced).** |
| Migrations | `python manage.py makemigrations --check --dry-run` | **No changes detected.** |
| Django tests | `python manage.py test` | **Ran 211 tests — OK (skipped=1)** in 268.29 s. |
| Pytest | `python -m pytest -q` | **210 passed, 1 skipped** in 296.12 s. |
| Whitespace | `git diff --check` | Exit 0 (only benign LF→CRLF notices). |
| CSS integrity | brace balance in `static/css/styles.css` (unchanged) | 389 `{` / 389 `}`. |

Counts increased by exactly the three new presentation tests (208 → 211 Django, 207 → 210 pytest). The
single skip is the MySQL/InnoDB row-lock concurrency test — **SQLite-only environment (ADR-003), so
the MySQL concurrency path was not exercised** and is not claimed as validated here.

---

## 6a. Browser verification

**Method (safe, no persisted data).** The dev server was not running and Phase 9 must not create real
availability/leave rows. So every clinic surface was rendered through the **Django test client inside a
single rolled-back `transaction.atomic()` block** (a temp DOCTOR user + speciality + doctor profile +
3 availability rules + 2 leave rows were created only inside the transaction), then the transaction was
rolled back — **0 rows remained afterwards** (`doctors 0 / rules 0 / leave 0 / spec 0`). The saved HTML
was loaded in the same headless Chrome (CDP `cdp.mjs`, Chrome 155) with the `/static/` references
rewritten to `file://` so the **real working-tree `static/css/styles.css`** applied. No real
appointment, email or production data was touched.

**Matrix:** 11 page-variants × 4 widths (390 / 768 / 1024 / 1440) = **44 renders**, plus reduced-motion,
scripting-disabled and keyboard-focus passes.

| Property | Result (all 44 renders) |
|---|---|
| Horizontal overflow | **0** on every page/width (`scrollWidth == innerWidth`) |
| `<h1>` count | exactly 1 per page |
| `section-rule` | 40 × 2 px, `rgb(14,165,168)`; present on list + form + invalid pages; **0 on confirm** pages |
| Scoped headers | availability 6/6, leave 4/4 |
| Stacking (390 px) | thead `position: absolute` (clipped), `td` `display: flex`, `::before` = "Day" / "Start" |
| Table region | `tabindex="0"`, `role="region"`, `aria-label` present |
| Forms | `novalidate`; labels + native `select`/`time`/`number`/`checkbox`/`date` types |
| Invalid submit | `.field--error` + `.field__error` message text rendered |
| Confirm accessible name | `aria-labelledby` matches the `h1` `id` |
| Empty states | `.empty.empty--inline` present ("You have no availability rules yet." / "You have no leave recorded.") |
| Keyboard focus | every focused control shows a 3 px `rgb(11,124,128)` outline |
| Console errors | **0** across all renders |
| Reduced motion | transition duration `1e-06s` |
| JS disabled | 6 scoped headers, 3 rows, 1 rule still render |
| Persistence after QA | **0** rows (rolled back) |

---

## 8. Unresolved issues / limitations

1. **MySQL/InnoDB concurrency not run** — SQLite-only (ADR-003); the skipped row-lock test is a
   pre-existing environment limitation, not a Phase 9 regression. Not claimed as validated.
2. **Shared field-error association (`templates/partials/_field.html`, Phase 3).** Django 5.2 adds
   `aria-invalid="true"` and `aria-describedby="id_<field>_error"` to the widget when a field has
   errors, **but `_field.html` renders the `.field__error` span without a matching `id`**, so the
   `aria-describedby` target does not exist and the error text is not programmatically linked. This
   affects all forms, is out of Phase 9 scope, and is recorded for the dedicated accessibility pass.
- Browser QA used test-client HTML rewritten to `file://` rather than the live server (server down;
  no real data may be created) — the HTML is server-accurate and styled by the working-tree CSS, but
  it was not served over HTTP.
- No screenshot/perceptual review — the executing model cannot read images, so only quantitative
  DOM/CSSOM metrics are reported.

---

## 9. Git / hygiene

- All pre-existing uncommitted work (Phases 1–8, untracked docs/skills) preserved untouched.
- No `git reset` / `clean` / `restore` / checkout, no staging, no commit, no push, no branch.
- No unrelated dashboards or booking templates modified.
- **Work stops after Phase 9, awaiting review.**
