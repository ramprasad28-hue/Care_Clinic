# Phase 10 — Dashboards (patient / doctor / receptionist / admin / landing) report

**Status:** complete — awaiting review. Nothing staged, committed, or pushed.

## 1. Scope derived from the implementation plan

Phase 10 of the Phase 7.5 "premium editorial" restyle covers the role dashboards in the
`dashboards/` app plus the dashboard-related selectors in `static/css/styles.css`.

`docs/phase-7.5-implementation-plan.md` §Phase 10 defines the phase as:

> **Intended result:** dense, practical, legible dashboards that share the editorial *type and colour*
> system **without** adopting the marketing layout. Stat cards, tables, filters, pagination, status
> actions refreshed but kept compact.
> **Reuse:** all dashboard partials + selectors. **Refine:** type/colour/spacing only. **Replace:**
> none. **Do not** push hero/band/editorial-cover styling into dashboards.

Decision **D9** reinforces this: *confirm "type + colour only" (recommended) — do **not** restyle
dashboards toward the marketing layout.* §4.6 adds: *keep density; preserve all partials and asserted
strings; row-actions and stacked tables intact.*

| Surface | Template | Route (name) | In scope | Covered |
|---|---|---|---|---|
| Landing / router | `no_dashboard.html` (fallback) | `dashboards:landing` | yes | yes |
| Patient dashboard | `patient_dashboard.html` | `dashboards:patient` | yes | yes |
| Doctor dashboard | `doctor_dashboard.html` | `dashboards:doctor` | yes | yes |
| Receptionist dashboard | `receptionist_dashboard.html` | `dashboards:receptionist` | yes | yes |
| Book on behalf | `receptionist_book.html` | `dashboards:receptionist_book` | yes | yes |
| Admin dashboard | `admin_dashboard.html` | `dashboards:admin` | yes | yes |
| Status action (POST only) | — (no template) | `dashboards:appointment_status` | yes | yes (tested) |
| Shared appointment table | `_appointment_table.html` | (partial) | yes | yes |
| Shared filter form | `_filters.html` | (partial) | yes | yes |
| Pagination | `_pagination.html` | (partial) | yes | yes |
| CSS selectors | `.dashboard__head`, `.stat-card`, `.table-wrap`, `.filters`, `.pagination`, `.row-actions` | `static/css/styles.css` | yes | yes |

`dashboards/urls.py` declares every route above under `app_name = "dashboards"`. There is **no**
separate landing *template* — `DashboardLandingView` redirects to the role dashboard and renders
`no_dashboard.html` only for an unrecognised role. There is no leave/availability surface in this
app (those live in `clinic/`, Phase 9).

---

## 2. Files changed (Phase 10) and purpose

| File | Phase 10 change |
|---|---|
| `dashboards/tests.py` | Added `DashboardPresentationTests` — 8 presentation/accessibility contract tests (see §7). |
| `docs/phase-7.5-dashboards-report.md` | This report (new). |

**No dashboard template and **no** CSS was changed in Phase 10.** The nine dashboard templates and the
dashboard selectors were **already brought into the editorial type/colour system earlier in this same
uncommitted Phase 7.5 body of work** (they are already modified vs `HEAD`). Inspection confirmed they
already satisfy every §Phase 10 directive, so Phase 10's contribution is **verification, contract
locking (tests), and this report** rather than further restyling. This is deliberate: §Phase 10 says
*"Refine: type/colour/spacing only. **Replace:** none"* and D9 says *do not restyle dashboards toward
the marketing layout.* Adding new structural devices (e.g. `section-rule` lead-ins) would be a
structural change, not a type/colour/spacing refinement, so it was **not** done (see §4).

**Verification that the in-scope surfaces already carry the system** (working-tree content, not a new
Phase 10 edit):

| File | Already-present editorial convention |
|---|---|
| `patient_dashboard.html` | `.container.dashboard` → `.dashboard__head` (h1 + lead), `.cluster.mb-5` CTAs (`btn--primary`/`btn--secondary`), `<section class="section" aria-labelledby>` with `h2` ids, `_appointment_table` (`show_actions=False`). |
| `doctor_dashboard.html` | `.dashboard__head`, `.pill` / `.pill--neutral`, secondary CTAs, three labelled sections (today / upcoming / past), shared `_empty.html` for the no-profile branch. |
| `receptionist_dashboard.html` | `.dashboard__head` with live counts, CTAs, `_filters.html`, `_appointment_table.html`, `_pagination.html`. |
| `admin_dashboard.html` | `.dashboard__head`, `.stat-grid`/`.stat-card`/`.stat-value`/`.stat-label`, `visually-hidden` stats heading, labelled breakdown + appointments sections, filters/table/pagination. |
| `no_dashboard.html` | `.notice` with `h1` "No dashboard" and a secondary "Return home" action. |
| `receptionist_book.html` | breadcrumb, `.page-head`, `.filters` GET form (`id_patient`/`id_doctor`), `.section-header`, `.date-nav`/`.date-chip`, `.slot-grid`/`.slot-option` radios (`value="{slot.pk}"`), `_field.html` for `reason`, `.empty.empty--inline` fallback. |
| `_appointment_table.html` | `.table-wrap.table-wrap--stack` with `tabindex="0" role="region" aria-label="Appointments"`, `th[scope="col"]`, `data-label` cells, `_status_badge`, `.row-actions` with `btn--ghost btn--sm`. |
| `_filters.html` | `.filters` GET form, `.filters__title`, `_field.html` per field, Apply/Reset actions. |
| `_pagination.html` | `nav.pagination[aria-label="Pagination"]` with Previous/Next + `.pagination__status`, only when >1 page. |
| `static/css/styles.css` | `.dashboard__head` (1081), `.stat-grid`/`.stat-card`/`.stat-value`/`.stat-label` (1085-1113), `.pagination`/`.pagination__status` (1119-1126), `.filters`/`.filters__grid`/`.filters__actions` (1033-1062), `.table-wrap`/`.table-wrap--stack`/`.data-table`/`cell-ref` (940-1028), `.row-actions` (986-993, `min-height:2rem`), `@media` stacking (996-1028) — all using the approved tokens and serif/sans/data type roles. |

No shared partial was modified (`_field.html`, `_form_errors.html`, `_empty.html` remain Phase 3-owned).
No `appointments/`, `clinic/`, `accounts/` or `website/` template was touched.

---

## 2a. Files changed (Phase 10)

| File | Phase 10 change |
|---|---|
| `dashboards/tests.py` | `+` `DashboardPresentationTests` (8 tests). |
| `docs/phase-7.5-dashboards-report.md` | This report (new). |

The nine dashboard templates and the dashboard CSS selectors were **not** changed by Phase 10 (they
already carried the editorial system from the shared Phase 7.5 work). See §1a rationale.

---

## 3. Dashboard pages / states covered

All states were rendered from the real views/templates and exercised at **390 / 768 / 1024 / 1440 px**
(12 states × 4 widths = **48 renders**), with a Django test client inside one rolled-back
`transaction.atomic()` (no rows persisted — see §9).

| State | Route | What was exercised |
|---|---|---|
| Patient dashboard (populated) | `dashboards:patient` | `.dashboard__head`, 2 CTA cluster, 2 labelled sections, stacked table (6 cols), rows. |
| Patient dashboard (empty) | `dashboards:patient` | `.empty.empty--inline` "No appointments to show." in both sections. |
| Doctor dashboard (populated) | `dashboards:doctor` | speciality pill, 3 labelled sections, status actions, 7-col tables. |
| Doctor — no profile | `dashboards:doctor` | shared `_empty.html` "No doctor profile" branch. |
| Receptionist dashboard | `dashboards:receptionist` | filters (6 fields), stacked table, pagination. |
| Receptionist dashboard (empty) | `dashboards:receptionist` (filtered) | filtered-to-zero empty state, filters retained. |
| Admin dashboard | `dashboards:admin` | 13 `.stat-card`s, labelled stats/breakdown/appointments sections, filters/table/pagination. |
| Landing fallback | `dashboards:landing` | `.notice` + `h1` "No dashboard" + home link. |
| Book on behalf (slots) | `dashboards:receptionist_book` | filter form, date-nav, 5 `.slot-option` radios with `value` PKs. |
| Book on behalf (no slots) | `dashboards:receptionist_book` | `.empty.empty--inline` "No open slots …". |
| Book-on-behalf (initial form) | `dashboards:receptionist_book` | selectors only, no slots section. |
| Permission denied | `dashboards:doctor` (as patient) | `403` page (`permissions.py`). |

---

## 4. Design changes and consistency with the approved direction

**No new visual change was required or made in Phase 10.** The dashboards already express the approved
**editorial *type + colour* system** while remaining intentionally dense:

- **Type**: single serif page-heading voice inherited on `h1`/`h2` (`--type-page-font` /
  `--type-section-font`); sans for UI/body; tabular numerals for times/quantities (`.num`,
  `.stat-value`); `.cell-ref` uses the data font. Confirmed in the browser probe (admin
  `.stat-value` resolves to the shared sans stack; times use `font-variant-numeric: tabular-nums`).
- **Colour**: `.stat-card` left accent = `rgb(14,165,168)` (brand teal, `--brand-500` ≡ `--brand-600`),
  `--shadow-sm` surface; status carried by the shared `_status_badge`; focus ring `--focus-color`
  `rgb(11,124,128)`.
- **Spacing**: `.dashboard__head` (`--sp-5`), `.section` (`--sp-7`), `.cluster.mb-5`, `.filters`
  (`--sp-4 --sp-5`), `.pagination` (`--sp-5`) — all token-driven.
- **No marketing-layout adoption**: dashboards use no hero/band/editorial-cover devices; **zero**
  `.section-rule` lead-ins appear on any dashboard (verified: `sectionRuleCount = 0` for all
  dashboard states at all widths). `.dashboard__head` keeps its tighter, rule-free head by intent
  (see `phase-7.5-editorial-labels-report.md`: *"`.dashboard__head` unchanged (no max-width;
  intentional)"*). This is the D9 "type + colour only" confirmation.

Consistency across the four role dashboards is confirmed: every role dashboard shares
`.dashboard__head` and exactly one `<h1>`; section headings are announced via `aria-labelledby`
matching an `h2` `id`; the receptionist/admin lists reuse the same `_filters` / `_appointment_table` /
`_pagination` partials.

---

## 5. Authorization and backend preservation checks

No backend code, model, migration, URL name, form field, selector, service or view was changed in
Phase 10. The existing role/ownership guarantees are covered by the pre-existing dashboard suite (all
green) and were re-confirmed during rendering:

- **Access matrix** (`DashboardAccessTests`): anonymous → redirect to login for every dashboard;
  each role gets `200` on its own dashboard and `403` on the other three (patient/doctor/receptionist/
  admin). A patient requesting `dashboards:doctor` rendered the **`403`** page in the QA run
  (`permissions.py:73 raise PermissionDenied`) — not merely a `200`.
- **Ownership / IDOR** (`PatientDashboardTests`, `DoctorDashboardTests`): a patient only sees own
  appointments; a doctor's queryset is scoped to the requesting doctor; a doctor POSTing to another
  doctor's appointment returns **`404`**; invalid/unknown status transitions are rejected through
  `appointments.services` (never a direct field write); GET on the status endpoint is `405`.
- **CSRF** (`test_csrf_enforced_on_status_post`): enforced (`403` without token).
- **Book-on-behalf** (`ReceptionistBookingForm` over `appointments` services): patient-only targeting,
  unknown doctor rejected, patient role cannot book on behalf (`403`).
- **Read-only safety** (`DashboardReadOnlyTests`): GET dashboards do not mutate appointment state.
- **Asserted template strings preserved** (spec §K.5): "No dashboard", "no doctor profile",
  `reverse("doctor_list")` link, patient full name, `value="{slot.pk}"` — all still present and
  asserted.

---

## 6. Responsive and accessibility results

Measured from the rendered DOM/computed styles at **390 / 768 / 1024 / 1440 px** (48 renders).

**Responsive**
- **Horizontal overflow: 0 px at every state × width** (`scrollWidth − innerWidth = 0`); no horizontal
  scrollbar anywhere.
- **Stacked tables** at 390 px: `thead` `position:absolute` (visually hidden to AT as a block),
  `tbody td` `display:flex` with `::before` label from `data-label` — confirmed for
  patient/doctor/receptionist/admin tables (e.g. patient table label provider = `"Reference"`;
  `theadPos="absolute"`, `firstTdDisplay="flex"`). No-JS: same stacking by CSS.
- Density preserved (no marketing blow-up): stat cards stay compact
  (`repeat(auto-fit, minmax(160px,1fr))`, `minmax(130px,1fr)` under the small-screen rule); tables keep
  the `sp-3/sp-4` cell rhythm.

**Accessibility**

- Exactly **one `<h1>` per page** on every state (including `403` and "No dashboard"); sections are
  named by their `h2` (`aria-labelledby` = `upcoming-heading`/`history-heading`,
  `today/upcoming/past-heading`, `stats/by-status/appointments-heading`).
- Appointment tables: `th[scope="col"]` on **all** columns (6/6 on patient, 7/7 on
  doctor/receptionist/admin), `data-label` on every cell, and the scroll container is a focusable,
  labelled region: `tabindex="0" role="region" aria-label="Appointments"`.
- `.row-actions` status buttons: rendered height **32 px** (≥ 32 px requirement met) with a visible
  focus ring on focus: `outline: 3px solid rgb(11,124,128)`.
- Pagination: `nav.pagination[aria-label="Pagination"]` with `Page 1 of 2` + a Next link (and Previous
  once a later page is requested); links are plain anchors → keyboard-operable.
- Filters: `.filters` GET form; 6 fields (receptionist/admin) / 3 fields (book-on-behalf); labels bound
  via `_field.html`.
- Empty states: `.empty.empty--inline` present for empty patient/receptionist lists, the no-profile
  doctor branch (`.empty` + "No doctor profile"), and the no-open-slots book-on-behalf branch.
- "No dashboard": `.notice` with `h1` "No dashboard" and a `home` link.
- **Reduced motion**: with `prefers-reduced-motion: reduce`, button transitions resolve to
  `1e-06s` (effectively off).
- **JavaScript disabled** (receptionist dashboard at 390 px): 7 `scope="col"` headers, 10 rows,
  pagination and filters all render; the dashboards require no JS.
- **Console errors: 0** across all 48 renders.

---

## 6a. Verification method (no screenshot inspection)

Browser QA used the offline recipe proven in Phase 9: each state was rendered server-side with the
Django test client inside one rolled-back `transaction.atomic()`, the `"/static/` references were
rewritten to the real `file:///…/Care_Clinic/static/` paths, and the resulting HTML was loaded in
headless Chrome (CDP) at each width. Computed styles and DOM attributes were read programmatically.

> **No visual screenshot inspection occurred** — the model cannot read image input, so the report
> relies on programmatic DOM/computed-style measurements plus the automated test suite. It does not
> claim pixel-perceptual review.

---

## 7. Test results

| Command | Result |
|---|---|
| `python manage.py check` | **System check identified no issues (0 silenced).** |
| `python manage.py makemigrations --check --dry-run` | **No changes detected.** |
| `python manage.py test` | **Ran 219 tests — OK (skipped=1)** in 282.7 s. |
| `pytest -q` | **218 passed, 1 skipped** in 309.7 s. |
| `git diff --check` | **exit 0** (only the usual LF→CRLF notices). |

- **Skipped test:** the single skip is the pre-existing **MySQL-only concurrency test** in
  `appointments/tests.py:764` (`@unittest.skipUnless(...)`), unchanged from baseline. Under **ADR-003**
  (SQLite only) this cannot run; **SQLite results do not prove MySQL/InnoDB concurrency behaviour.**
- The full dashboard suite (existing `DashboardRoutingTests`, `DashboardAccessTests`,
  `PatientDashboardTests`, `DoctorDashboardTests`, `ReceptionistDashboardTests`,
  `ReceptionistBookOnBehalfTests`, `AdminDashboardTests`, `DashboardReadOnlyTests`) is included in the
  green run.

**New tests added — `dashboards/tests.py` → `DashboardPresentationTests` (8):**

1. `test_dashboards_use_shared_head_scaffold_and_single_h1` — patient/doctor/receptionist/admin all
   render `.dashboard__head` and exactly one `<h1>`.
2. `test_doctor_sections_are_labelled_by_their_headings` — `aria-labelledby` ↔ `h2` ids for
   today/upcoming/past.
3. `test_appointment_table_is_focusable_labelled_stacked_region` — `.table-wrap.table-wrap--stack`,
   `tabindex="0"`, `role="region"`, `aria-label="Appointments"`, all six `th[scope="col"]`,
   `data-label` cells.
4. `test_pagination_renders_as_labelled_nav_when_paged` — `aria-label="Pagination"` + `Page 1 of 2` +
   Next, and Previous on page 2.
5. `test_status_actions_use_compact_ghost_buttons` — `btn btn--ghost btn--sm` on doctor status actions.
6. `test_admin_stat_cards_render_editorial_tokens` — `.stat-grid` / `.stat-card` / `.stat-value` /
   `.stat-label`.
7. `test_doctor_without_profile_uses_shared_empty_state` — `.empty` + "No doctor profile".
8. `test_no_dashboard_renders_notice_with_home_link` — `.notice` + `<h1>No dashboard</h1>` + home URL.

These lock the **presentation/accessibility contracts** (not new behaviour) the editorial direction
depends on, mirroring the Phase 8/9 approach.

---

## 8. Migration and diff-check results

- `makemigrations --check --dry-run` → **No changes detected** (ADR-019: the `dashboards` app has no
  models/migrations; nothing added).
- `git diff --check` → **exit 0**; output contains only benign `LF will be replaced by CRLF` warnings,
  no whitespace errors.

---

## 9. Limitations and unverified behaviour

- **No screenshot/perceptual review** (model cannot read images); findings are from DOM/computed-style
  probes + the automated suite. A human visual pass is still advisable.
- **MySQL/InnoDB concurrency is unverified** (ADR-003 → SQLite only); the one skip is the MySQL-only
  concurrency test.
- The QA used `file://`-rewritten static paths; this exercises the real CSS/JS artefacts but is **not**
  the live dev server. The `http://127.0.0.1:8017/` dev server was **not** running this session, so no
  live-server request trace was taken.
- `receptionist_book.html` still hand-writes its three selector fields (label + `<select>`) instead of
  `_field.html` because the options are dynamic and must preserve `selected` state; this duplication is
  pre-existing and was not changed (out of the "type + colour only" remit).
- **Shared `_field.html` limitation (pre-existing, Phase 3):** on invalid bound fields Django 5.2 emits
  `aria-invalid="true"` + `aria-describedby="id_<field>_error"`, but `_field.html` renders `.field__error`
  without a matching `id`, so the reference can dangle. Recorded here for continuity; not refactored.
- Empty `.empty--inline` states are heading-free by design (outline-safe after an `h1`/`h2`).

## 10. Remaining issues and recommended follow-ups

- No defects found in the Phase 10 scope; there are no blocking follow-ups.
- Optional, out-of-scope cleanups if a later phase wants them: (a) give `.field__error` an `id` to
  satisfy the dangling `aria-describedby` (shared partial → its own phase); (b) consider whether
  `receptionist_book.html`'s hand-rolled selectors could adopt a shared select field renderer.
- `docs/implementation-roadmap.md` does not yet list the Phase 7.5 sub-phases; a documentation-only
  reconciliation is deferred (plan D10 / Phase 14).

---

## Git status and changed files (this phase)

### Phase 10 changes
```
 M dashboards/tests.py                       (+ DashboardPresentationTests, 8 tests)
?? docs/phase-7.5-dashboards-report.md        (this report, new)
```

### Pre-existing uncommitted work preserved (unchanged by Phase 10)

The dashboard templates and CSS were already modified in the current uncommitted Phase 7.5 body of
work; Phase 10 left them untouched:

```
 M dashboards/templates/dashboards/_appointment_table.html
 M dashboards/templates/dashboards/_filters.html
 M dashboards/templates/dashboards/_pagination.html
 M dashboards/templates/dashboards/admin_dashboard.html
 M dashboards/templates/dashboards/doctor_dashboard.html
 M dashboards/templates/dashboards/no_dashboard.html
 M dashboards/templates/dashboards/patient_dashboard.html
 M dashboards/templates/dashboards/receptionist_book.html
 M dashboards/templates/dashboards/receptionist_dashboard.html
 M static/css/styles.css
```

The full uncommitted working tree also contains the earlier-phase work (accounts/booking/clinic
templates, `templates/base.html`, `templates/home.html`, `website/*`, `docs/*` reports, untracked
`.agents/`, `templates/partials/`, `static/js/`, and the Phase 7.5 planning/spec docs). **All of it is
preserved.** Nothing was staged, committed, or pushed.
