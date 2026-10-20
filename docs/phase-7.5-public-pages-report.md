# Phase 7.5 — Phase 6 (Public Listing & Detail Pages) — Report

> **Date:** 2026-10-18
> **Project:** `C:\Users\Ramprasad\OneDrive\Desktop\Care_Clinic`
> **Phase:** 7.5 / Phase 6 — align the public speciality and doctor listing/detail pages with
> the premium-editorial system established on the homepage.
> **Application files changed:** `website/templates/website/speciality_list.html`,
> `website/templates/website/speciality_detail.html`, `website/templates/website/doctor_list.html`,
> `website/templates/website/doctor_detail.html`, `static/css/styles.css`.
> **Deliverable:** this report (`docs/phase-7.5-public-pages-report.md`).
> **Nothing committed or pushed.** No work after Phase 6 started. No backend, model, view, form,
> URL, migration, setting, dependency or JavaScript file was changed.
> **Skills applied:** `design-taste-frontend` (project-local, `.agents/skills/design-taste-frontend`)
> for the house rules; `frontend-design`, `web-design-guidelines` (used across 7.5).

---

## 1. Scope

The Phase 7.5 plan (`docs/phase-7.5-implementation-plan.md` §"Phase 6") names four files:
`speciality_list.html`, `speciality_detail.html`, `doctor_list.html`, `doctor_detail.html` +
`static/css/styles.css`, and the intended result: *"use the editorial page-head grammar, refined
filter bar, pill meta, `.detail-list`, and the availability table — consistent with home."*

| Surface | Route | In scope | Covered |
|---|---|---|:--:|
| Speciality listing | `/specialities/` | yes | ✅ |
| Speciality detail | `/specialities/<slug>/` | yes | ✅ |
| Doctor listing | `/doctors/` | yes | ✅ |
| Doctor detail | `/doctors/<slug>/` | yes (plan Phase 6 file list) | ✅ |
| Home | `/` | no (Phase 5) | touched only via shared CSS tokens — no home markup changed |
| Auth / booking / dashboards / clinic | — | no (Phases 7–9) | untouched |

The task brief's "Focus on" list named the first three surfaces explicitly; the assurance plan's
Phase 6 file list also names `doctor_detail.html` and its "pill meta / `.detail-list` / availability
table" intent, so it is included here and flagged as such.

**No new primitives were introduced** (plan: *"Introduce: none"*). The changes reuse
`.section-rule` (Phase 2), `.section-title` (Phase 2), and the existing `.cluster` utility.

---

## 1a. Files changed

| File | Change |
|---|---|
| `website/templates/website/speciality_list.html` | Added `<span class="section-rule" aria-hidden="true">` as the page-head lead-in above the `h1`. |
| `website/templates/website/doctor_list.html` | Same page-head rule lead-in above `h1`. |
| `website/templates/website/speciality_detail.html` | Rule added to the page-head; the doctors section header converted to the editorial grammar (`section-rule` + `h2.section-title`, `id="doctors-heading"` kept). |
| `website/templates/website/doctor_detail.html` | Rule added above the `h1`; the pill row wrapped as `<p class="cluster">` for even meta spacing (same pills, same order). |
| `static/css/styles.css` | `.page-head .section-rule` spacing; `.filter-bar` flattened to a ruled strip; `.pill` padding/line-height refined; mobile padding override localised to `.filters`. |
| `docs/phase-7.5-public-pages-report.md` | This report (new). |

No partial was modified (Phase 3 owns them); no parent other than the four above.

---

## 2. Design direction applied — the editorial page-head grammar

Home's labelled bands use one reusable header block: a short teal rule + a sentence-case label +
a serif heading + a lede. Phase 6 extends the same **structural** grammar to the public
page-level headers without inventing copy or adding primitives:

- **Rule** — `<span class="section-rule" aria-hidden="true">` (40 × 2 px, `--brand-600`), the same
  print/journal lead-in used on the home bands. Decorative, so `aria-hidden`.
- **Serif H1** — unchanged `h1` display role (`--type-page-font`, serif stack).
- **Measure** — the intro paragraph keeps `--measure-body` inside a `--measure-heading` wrapper,
  the same pair used by `.band__head`, so all page intros share one measure.
- **Section header** — on `speciality_detail`, the inner "Doctors in this speciality" heading
  becomes a real section header (rule + `h2.section-title`), matching the home specialities/doctors
  bands.

No eyebrow/kicker was introduced on the listing pages: the home eyebrow *names* a band above a
longer heading, whereas a listing already has its title as the `h1`; adding a label would duplicate
it or invent copy (content rule §J).

---

## 3. Per-template changes

### `speciality_list.html`
```diff
 <div class="page-head">
+    <span class="section-rule" aria-hidden="true"></span>
     <h1>Specialities</h1>
```
Grid (`service-grid` + `_speciality_card`) and the `_empty.html` fallback are unchanged.

### `speciality_detail.html`
```diff
 <div class="page-head">
+    <span class="section-rule" aria-hidden="true"></span>
     <h1>{{ speciality.name }}</h1>
 ...
 <section aria-labelledby="doctors-heading">
-    <h2 id="doctors-heading">Doctors in this speciality</h2>
+    <span class="section-rule" aria-hidden="true"></span>
+    <h2 class="section-title" id="doctors-heading">Doctors in this speciality</h2>
```
Breadcrumb, `aria-labelledby`, doctor loop and the `level=3` empty state are unchanged.

### `doctor_list.html`
```diff
 <div class="page-head">
+    <span class="section-rule" aria-hidden="true"></span>
     <h1>Doctors</h1>
```
Filter form (`role="search"`, `label[for="speciality"]`, `select[name="speciality"]`,
`data-autosubmit`, submit button) and the "Clear filter" empty state are unchanged.

### `doctor_detail.html`
```diff
 <div class="page-head mb-4">
+    <span class="section-rule" aria-hidden="true"></span>
     <h1>Dr. {{ doctor.user.get_full_name }}</h1>
-    <p>
+    <p class="cluster">
         <span class="pill">{{ doctor.speciality.name }}</span>
```
The `.cluster` utility (existing flex-wrap helper) gives the meta pills consistent spacing;
`.detail-list`, the "Book appointment" CTA and the stacked availability table are untouched.

---

## 4. CSS refinements (in place, tokens only)

| Selector | Before | After |
|---|---|---|
| `.page-head .section-rule` | (none) | new: `margin-bottom: var(--sp-4)` (16 px) — only applies on pages that opt into a rule |
| `.filter-bar` | boxed panel: `background: var(--paper)`, `border: 1px`, `border-radius`, `box-shadow: var(--shadow-sm)`, `padding: sp-4 sp-5`, `margin-bottom: sp-5` | flat ruled strip: transparent, `border-top`/`border-bottom: 1px solid var(--line)`, no radius, no shadow, `padding: sp-4 0`, `margin-bottom: sp-6` |
| `.pill` | `padding: 0.2rem 0.6rem` | `padding: 0.28rem 0.7rem; line-height: 1.5` |
| `@media (max-width: 640px)` | `.filters, .filter-bar { padding: var(--sp-4); }` | `.filters { padding: var(--sp-4); }` (dashboards unchanged; `.filter-bar` keeps its `sp-4 0`) |

No new colour, font, radius, shadow or motion tokens were added. `.page-head` and `.page-head p`
base rules were left as they are (they are shared with appointments/clinic/dashboard pages), so
those out-of-scope pages are unaffected — verified below.

---

## 5. Compatibility preserved (spec §K)

- **URLs** unchanged; no view, form, model or migration touched (`makemigrations --check` → none).
- **Context variables** unchanged (`specialities` / `speciality`+`doctors` / `doctors`,
  `specialities`, `selected_speciality` / `doctor`).
- **Form field names** intact: `select[name="speciality"]`, `label[for="speciality"]`,
  `data-autosubmit` still present (verified in DOM).
- **Behaviour** unchanged: `doctor.get_absolute_url`, `speciality.get_absolute_url`,
  `appointments:book` CTA, breadcrumb `aria-current="page"`, and the `_empty.html` states.
- **No invented content** — all added markup is structural (rules, class names); no new prose,
  numbers, credentials, ratings or media.
- One `h1` per page; heading order verified (`h1` → section `h2` → entry `h3`).

---

## 5. Validation

| Command | Result |
|---|---|
| `python manage.py check` | `System check identified no issues (0 silenced).` |
| `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| `python manage.py test` | **OK**, 205 tests, `skipped=1` (222.60 s) |
| `pytest -q` | **204 passed**, 1 skipped (273.69s) |
| `git diff --check` | exit 0 (only pre-existing `core.autocrlf` LF→CRLF advisories) |
| CSS brace balance | `{` 388 / `}` 388 |

Environment: `C:\venvs\anmaya-clinic\Scripts\python.exe` (Python 3.12), Django dev settings.
The tracebacks printed mid-run are the expected `PermissionDenied` / 404 negative-path tests.

---

## 5a. Browser verification

Tooling: the repository's own `design-taste-frontend` CDP driver
(`.agents/skills/design-taste-frontend/scripts/lib/cdp.mjs`) driving installed Chrome
(`C:\Program Files\Google\Chrome\Application\chrome.exe`, Node v22.23.1); live dev server on
`http://127.0.0.1:8017/`. Screenshots + JSON: `.taste-skill/inspect/phase6/`.

Pages: `/specialities/`, `/specialities/cardiology/`, `/doctors/`, `/doctors/aswin-kumar/`
(real public slug discovered at runtime), each at **390 / 768 / 1024 / 1440** (16 passes),
plus reduced-motion (2) and JS-disabled (2) passes.

| Check | Result |
|---|---|
| Horizontal overflow (`scrollWidth − clientWidth`) | **0 px** on every page × width |
| Exactly one `h1` per page | yes (16/16), and it is the first heading |
| `h1` type role | serif stack on every page (`ui-serif, "Iowan Old Style", "Palatino…, serif`) |
| Page-head rule present | yes on all four pages; 40 × 2 px, `rgb(14,165,168)` (`--brand-600`), `margin-bottom` 16 px |
| Intro measure | `--measure-body` (≈500 px at 1440) inside a `--measure-heading` wrapper |
| `speciality_detail` section header | `h2.section-title` "Doctors in this speciality" present |
| `doctor-list` filter bar | flat: `border-top`/`border-bottom: 1px`, `box-shadow: none`, `border-radius: 0`, transparent, `padding: 16px 0` |
| Doctor-detail pill meta | 2 pills, `padding 4.48 × 11.2 px`, `line-height 19.2px`, `--brand-050` / `--brand-700` |
| Breadcrumb + `aria-current` | present on both detail pages |
| Heading order | `h1` → `h2`/`h3` logical on every page |
| Console errors | 0 on every page × width |
| Link integrity | 18 unique internal links followed → **all 200** |
| `prefers-reduced-motion: reduce` | media matches; rule and card `transition-duration` collapse to `1e-06s` |
| JavaScript disabled | pages render, rule present, `h1 = 1`, cards present, no overflow |

**Perceptual review limitation.** Screenshots were captured as required, but the model answering
this task **cannot read image input**, so no visual/perceptual judgement of them was performed.
Every finding above is a quantitative DOM/CSSOM measurement. This is stated rather than claiming a
visual review that did not happen.

*Tooling note:* the CDP `browser.close()` did not let Node exit cleanly on this machine (the shell
hit its timeout after all output and `report.json` were written) — a harness quirk, not a page
error (the page-level `consoleErrors` were empty).

---

## 6. Documentation gaps observed (reported, not fixed)

Per the task, these were checked and are **not** fixed here (out of Phase 6 scope):

- `docs/phase-7.5-homepage-hero-report.md` — **missing** (the Plan P4 / hero deliverable; noted as
  outstanding in `docs/hospic-to-care-clinic-implementation-plan.md` §4, row "Homepage-hero report").
- A standalone **Phase 5 (home bands) report** is **missing** (only the Stage-5 *code* landed; no
  report file exists alongside `phase-7.5-typography-report.md` / `phase-7.5-editorial-labels-report.md`
  / `phase-7.5-editorial-cards-report.md`).
- `docs/implementation-roadmap.md` does not carry the 7.5 stage entries (P1–P6); flagged for a
  later documentation pass.

---

## 7. Deferred / notes

1. **No new primitives** were needed (plan: "Introduce: none") — the rule, section title and
   `.cluster` already existed.
2. `.pill` is shared with `appointment_book.html` and `doctor_dashboard.html`; the refinement is a
   small, uniform size bump (more padding + explicit line-height) and is consistent everywhere.
3. `.filter-bar` is used **only** by the public doctor list; the dashboard equivalent uses
   `.filters`, which was left untouched.
4. `.page-head` base rule was deliberately not changed (it is used by appointments/clinic/dashboard
   pages); only the opt-in `.page-head .section-rule` spacing was added.

---

## 8. Git status

`git status --short` inspected; **no staging, commit, branch or push** was performed and no
pre-existing uncommitted work was altered. Tracked files changed by this phase:
`static/css/styles.css` and the four `website/templates/website/*.html` files (all previously
modified in the working tree). `templates/partials/` and `static/js/` remain **untracked**.
Work stops here for review — Phase 7 (auth pages) is not started.
