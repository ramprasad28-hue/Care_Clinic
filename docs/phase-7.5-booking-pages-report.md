# Phase 8 — Booking Pages Report

> **Phase:** Phase 8 (booking flow) of the Phase 7.5 "premium editorial" restyle.
> **Deliverable:** this report — `docs/phase-7.5-booking-pages-report.md`.
> **Application files changed:** `appointments/templates/appointments/appointment_book.html`,
> `appointment_reschedule.html`, `appointment_detail.html`, `appointment_list.html`,
> `appointments/tests.py`, `static/css/styles.css`.
> **Formatting rule:** presentation-only. No model, migration, view, form, service, selector, URL,
> setting or JavaScript file was changed. `appointment_cancel.html` and `_status_badge.html` were
> inspected and intentionally left unchanged in Phase 8 — they already carry the editorial
> `confirm` panel and text+dot `badge` treatment from an earlier phase.

---

## 1. Scope

The Phase 7.5 plan (Phase 8) names the booking family and the CSS file:

| Surface | Route (name) | In scope | Covered |
|---|---|---|:--:|
| Booking | `/appointments/book/<slug>/` (`appointments:book`) | yes | yes |
| Cancel | `/appointments/<reference>/cancel/` (`appointments:cancel`) | yes | reviewed — no change needed |
| Reschedule | `/appointments/<reference>/reschedule/` (`appointments:reschedule`) | yes | yes |
| Listing | `/appointments/` (`appointments:list`) | yes | yes |
| Detail | `/appointments/<reference>/` (`appointments:detail`) | yes | yes |
| Status badge partial | `_status_badge.html` | yes (refine if needed) | inspected — no change |

Plan directives honoured: **Reuse** the slot-grid markup, `novalidate` + `_field.html` +
`_form_errors.html`, `_status_badge.html`, and `data-guard`. **Refine** the slot grid, ticket and
badges. **Replace:** none. **Introduce:** none.

---

## 1a. Files changed

| File | Change |
|---|---|
| `appointment_book.html` | `section-rule` lead-in above the `h1`; second rule + `h2.section-title id="date-heading"` for *"Choose a date"*; rule + `h2.section-title id="slot-heading"` for *"Available slots on …"*. |
| `appointment_reschedule.html` | Same page-head rule above `h1`; rule + section-title for *"Choose a new date"*; rule + section-title for *"New slot on …"*. |
| `appointment_detail.html` | Rule above `h1`; rule + section-title for *"More information"*; rule + section-title (`id="actions-heading"`) for *"Manage this appointment"*. |
| `appointment_list.html` | Rule above `h1` only (the table + filter pills were already editorial-consistent). |
| `static/css/styles.css` | `.slot-option` gained `min-height: 2.75rem` and a tokenised selected ring; `.ticket` flattened (shadow removed); `.badge` padding/line-height aligned to `.pill`. |
| `appointments/tests.py` | Three regression tests added (see §5). |
| `docs/phase-7.5-booking-pages-report.md` | This report (new). |

No shared partial was modified (Phase 3 owns `_field.html` / `_form_errors.html` / `_empty.html`),
and `appointment_cancel.html` / `_status_badge.html` were left untouched.

---

## 1a. Design direction applied

The booking screens now use the same **editorial page-head grammar** as the public pages: a short
teal rule (`<span class="section-rule" aria-hidden="true">`, 40 × 2 px, `--brand-600`) leads the
display heading, and each major region opens with the same rule + `h2.section-title` pairing used by
the home bands. The cancel page deliberately keeps its single-purpose `.confirm` treatment (no rule:
a destructive confirmation is not a browsing section).

The status badge already carried **text + dot** (never colour alone); only its metrics were tightened
so badges and pills share one baseline. The `.ticket` motif keeps its 6 px teal rail and radius but
now sits flat in the page like every other Phase 3 card (no shadow).

---

## 2. Presentation changes (reuse, refine)

### Slot grid (`.slot-grid` / `.slot-option`)

- Grid column count is unchanged (`repeat(auto-fill, minmax(140px, 1fr))`); each `.slot-option`
  remains a single `<label>` wrapping the radio + time, so the whole chip is one hit target.
- Added `min-height: 2.75rem` (44 px) so every slot tile meets the minimum touch-target size at all
  widths without changing its padding.
- The selected ring now uses the design token `--brand-200` (`box-shadow: 0 0 0 2px var(--brand-200)`)
  instead of the previous hard-coded `rgba(14, 130, 141, 0.2)`. This is a colour-value substitution
  of an existing decoration — the selected state already existed and its border/background are
  unchanged.
- No markup change: the radio still renders `value="{slot.pk}"`, `name="slot"`, inside
  `label.slot-option`.

### Ticket (appointment detail / confirmation motif)

- Removed `box-shadow: var(--shadow-md)`. `.ticket` now sits flat on the page like the rest of the
  editorial card system (border + radius + 6 px teal spine retained).

### Status badge

- `.badge` padding standardised to `0.28rem 0.7rem` and `line-height: 1.5`, matching `.pill`, so
  status badges and meta pills share one rhythm. Status classes still pair a tint with a text
  colour, and the dot + label text keep the state legible without colour.

### Editorial page-head grammar

- `section-rule` + `section-title` added at the page head and at each real section boundary on the
  booking, reschedule and detail surfaces (see §1a table), matching the public/home grammar.

---

## 3. Preserved backend contracts

Nothing below was touched (verified by diff — only the six files in §1a changed):

- `Appointment` / `AppointmentSlot` models, DB `CheckConstraint` (`appt_end_after_start`) and the
  `OneToOneField` slot uniqueness guarantee.
- `appointments/services.py`: `book_slot` / `cancel_appointment` / `reschedule_appointment` /
  `transition_status`, `transaction.atomic()`, `select_for_update()` slot locking, state
  transitions, reference generation, and the `can_book_for`/`can_cancel`/`can_reschedule` rules.
- Ownership scoping (`Appointment.objects.for_user`) → IDOR still returns 404.
- URL contracts and names (`appointments:list/book/detail/cancel/reschedule`).
- Forms (`BookingForm`, `RescheduleForm`, `CancelForm`) and `available_slots` (OPEN slots only).
- Server-side validation is never bypassed: forms keep `novalidate` (which only disables *browser*
  validation) and `data-guard` (double-submit guard); errors still render server-side.

---

## 4. Accessibility & interaction checks

- **Slot semantics preserved** — one radio per slot, `name="slot"`, `value` = slot PK, wrapped by
  `label.slot-option` (single shared hit target per option). Confirmed in rendered HTML.
- **Selected state** — not colour-only: border becomes `--brand-600`, background `--brand-050`,
  plus a `--brand-200` ring; the radio control itself is also visually checked.
- **Keyboard/focus** — `.slot-option:focus-within` keeps the 3 px `--focus-color` outline;
  radios are natively focusable and arrow-key navigable within the fieldset.
- **Form errors** — invalid submission renders one `role="alert"` message plus an inline
  `.field__error` ("This field is required.") and focus moves to the first errored field (existing
  `app.js` behaviour). Headings, `label[for]` associations and `.field__label` legends intact.
- **Status never colour-only** — `.badge` renders a dot (`aria-hidden`) plus the status label text.
- **Reference visible** — the appointment reference renders in `.ticket__ref` on detail (and in the
  cancellation confirmation text / breadcrumb elsewhere).
- **Reduced motion** — with `prefers-reduced-motion: reduce`, the `.slot-option` transition duration
  collapses to ~0 s; no animation-only affordances are used.
- **No-JS** — with scripting disabled the page keeps `.no-js`, renders all 28 slot radios, and has
  no overflow; selection works with the radios alone.

> Known shared limitation (unchanged, carried from Phase 7): inline field errors are not wired to
> inputs via `aria-describedby`/`aria-invalid`. That lives in the Phase 3 partial
> `templates/partials/_field.html` and is out of scope for Phase 8; recorded for a later
> dedicated accessibility pass.

---

## 5. Regression tests added (`appointments/tests.py`)

| Test | Guards |
|---|---|
| `BookingViewTests.test_booking_form_preserves_slot_value_and_guards` (new) | slot radios keep `name="slot"` and `value="{slot.pk}"`; form keeps `novalidate` + `data-guard`. |
| `AppointmentListDetailViewTests.test_owner_can_view_detail` (extended) | detail shows the appointment **reference** and the doctor full name. |
| `CancelRescheduleViewTests.test_cancel_page_keeps_reference_and_guards` (new) | cancel keeps `novalidate` + `data-guard` and shows the reference. |
| `CancelRescheduleViewTests.test_reschedule_form_preserves_slot_value_and_guards` (new) | reschedule keeps `name="slot"`, `value="{slot_b.pk}"`, `novalidate` + `data-guard`. |

The existing `test_patient_can_view_booking_page` already asserts the doctor full name on the
booking page.

---

## 6. Validation results

| Check | Command | Result |
|---|---|---|
| System check | `python manage.py check` | **No issues (0 silenced).** |
| Migrations | `python manage.py makemigrations --check --dry-run` | **No changes detected.** |
| Django tests | `python manage.py test` | **Ran 208 tests — OK (skipped=1)** in 210.27 s. |
| Pytest | `python -m pytest -q` | **207 passed, 1 skipped** in 226.74 s. |
| Whitespace | `git diff --check` | Exit 0 (only benign LF→CRLF notices). |
| CSS integrity | brace balance in `static/css/styles.css` | 389 `{` / 389 `}`. |

The single skip is the MySQL/InnoDB row-lock concurrency test — **SQLite-only environment (ADR-003),
so the MySQL concurrency path was not exercised** and is not claimed as validated here.

### Backend functionality preserved

- All 208 Django / 207 pytest tests pass, including the full booking, cancellation, rescheduling,
  status-transition, ownership-scoping and HTTP-flow suites — unchanged.
- No behavioural change: only presentation attributes and three additive assertions were introduced.

---

## 7. Browser verification

**Method (safe, no persisted data).** The live dev server was not running, and Phase 8 must not
create real appointments. So every booking surface was rendered through the **Django test client
inside a single rolled-back `transaction.atomic()` block** (a temp patient + one CONFIRMED
appointment were created only inside the transaction; the slot grid, the "no slots on this date"
inline empty state, the invalid-submit error state, the "no availability" empty state, list, detail,
cancel and reschedule were all captured), then the transaction was rolled back — **0 appointments
remained afterwards** ("remaining appointments: 0"). The saved HTML was loaded in the same headless
Chrome (CDP `cdp.mjs`) with a `<base>` pointing at the project root so the **real working-tree
`static/css/styles.css`** applied. No email/notification/booking was ever persisted.

**Matrix:** 8 page-states × 4 widths (390 / 768 / 1024 / 1440) = **32 renders**, plus a
reduced-motion pass and a scripting-disabled pass.

| Property | Result (all 32 renders) |
|---|---|
| Horizontal overflow | **0** on every page/width |
| `<h1>` count | exactly 1 per page |
| `section-rule` | 40 × 2 px, `rgb(14,165,168)` (`--brand-600`); book/reschedule/detail = 3, list = 1, cancel = 0, no-availability = 1 |
| Slot grid columns | 390 → 2, 768 → 4, 1024 → 6, 1440 → 7 (auto-fill) |
| `.slot-option` min-height | `44px` at all widths |
| Slot radios | `name="slot"`, `value` = slot PK, wrapped in `label.slot-option` |
| Selected slot (probe) | border `rgb(14,165,168)`, bg `rgb(232,248,248)`, box-shadow `rgb(207,238,238) 0 0 0 2px` |
| `.ticket` | `box-shadow: none`; `ticket__ref` = appointment reference |
| `.badge` | padding `4.48px 11.2px`, line-height `19.2px`; dot + label text present |
| Invalid submit | 1 `role="alert"`, inline `.field__error` "This field is required." |
| Empty states | `.empty.empty--inline` (no open slots on date); `.empty` + `h2` "No availability yet" |
| Forms | booking / reschedule / cancel carry `novalidate` + `data-guard` |
| Labels | every `label[for]` resolves to an element |
| Console errors | **0** across all renders |
| Reduced motion | slot transition duration ≈ `1e-06s` |
| JS disabled | `.no-js` retained, 28 slot radios render, overflow 0 |

Note: the sole "overflow candidate" at 390 px on the list page is a `<th>` inside the
visually-hidden stacked `.table-wrap--stack` header (`clip`/`position:absolute`), which is clipped
and does not affect document `scrollWidth` — hence page-level overflow remains 0.

**Measurement caveat.** The first pass read the selected-slot computed style in the same JS turn as
the programmatic `checked` change; Chrome applies `:has()` style invalidation after that turn, so the
first read looked unselected. A follow-up probe re-read after a frame and confirmed the correct
selected styling (table above). Styling was never changed as a result.

---

## 8. Unresolved issues / limitations

1. **MySQL/InnoDB concurrency not run** — SQLite-only (ADR-003); the skipped row-lock test is a
   pre-existing environment limitation, not a Phase 8 regression. Not claimed as validated.
2. **Shared field-error association** — inline errors still lack `aria-describedby`/`aria-invalid`
   (`templates/partials/_field.html`, Phase 3). Deferred to a dedicated accessibility pass.
3. **Browser QA used test-client HTML, not the live server** — the dev server was not running and no
   real appointment may be created, so rendering went through a rolled-back transaction; the HTML is
   server-accurate and styled by the working-tree CSS, but it was not served over HTTP.
4. **No screenshot/perceptual review** — the executing model cannot read images, so only
   quantitative DOM/CSSOM metrics are reported.

---

## 9. Git / hygiene

- All pre-existing uncommitted work (Phases 1–7, untracked docs/skills) preserved untouched.
- No `git reset` / `clean` / `restore` / checkout, no staging, no commit, no push, no branch.
- No unrelated dashboards/clinic templates modified.
- **Work stops after Phase 8, awaiting review.**
