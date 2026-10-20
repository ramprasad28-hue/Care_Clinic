# Care_Clinic Homepage — H1 Baseline Report

> **Type:** Inspection / baseline only. **No application code, template, stylesheet,
> script, test, setting, model, migration, or dependency was changed.** Nothing was
> staged, committed, or pushed. H2 was **not** started (see §14).
> **Date:** 2026-10-18
> **Project:** `C:\Users\Ramprasad\OneDrive\Desktop\Care_Clinic`
> **Primary plan:** `docs/homepage-reference-analysis-and-execution-plan.md`
> **Evidence tags:** **[observed]** (measured/read this session), **[inference]**,
> **[assumption]** (unverified).

---

## 1. H1 scope and objective

**Objective (as instructed for this task):** establish the current state of the homepage
and identify the exact visual gaps the approved implementation plan intends to address.

**Scope H1:** preserve the repository; read the documentation; inspect the homepage files;
establish a rendered baseline at 390 / 768 / 1024 / 1440 px if the environment allows;
identify visual gaps; run the light validation commands; write this report. **No code
changes.**

> **Noted discrepancy [observed]:** the primary plan
> (`docs/homepage-reference-analysis-and-execution-plan.md` §8) labels **H1** as a *code*
> phase — *"Normalise the About band header to the shared `.band__head` grammar."* The
> current task instead defines **H1 as an inspection/baseline phase** and forbids code
> changes. This report follows the **task** definition (baseline, no code). The plan's
> intended H1 change is carried forward into later-phase recommendations (§9, item R1).

---

## 2. Git status before inspection

Branch `main`; HEAD `d474971`. **Nothing staged** (`git diff --cached --name-only` empty);
**no stashes** (`git stash list` empty).

**Tracked modifications (` M`) — pre-existing Phase 7.x work (40 files):**
`README.md`; `accounts/forms.py`; all `accounts/templates/accounts/*.html` (8);
all `appointments/templates/appointments/*.html` (6) + `appointments/tests.py`;
all `clinic/templates/clinic/*.html` (6) + `clinic/tests.py`;
all `dashboards/templates/dashboards/*.html` (9 incl. partials) + `dashboards/tests.py`;
`docs/architecture.md`, `docs/decisions.md`, `docs/implementation-roadmap.md`;
`static/css/styles.css`; `templates/base.html`; `templates/home.html`;
`website/templates/website/*.html` (4); `website/tests.py`; `website/views.py`.

**Untracked (`??`):** `.agents/`, `.taste-skill/`, `skills-lock.json`,
`static/js/`, `templates/partials/`, and the `docs/*` analysis/report set
(incl. `docs/homepage-reference-analysis-and-execution-plan.md`).

All of the above were **preserved exactly**; no discard/reset/clean/stash was used.

---

## 3. Documentation inspected

- `docs/homepage-reference-analysis-and-execution-plan.md` (primary plan — read in full).
- `docs/frontend-design-specification.md` (read in full; §E homepage mapping, §J content
  rules, §K contracts, Appendices).
- `docs/phase-7.5-implementation-plan.md` (read in full; baseline §1.5, verification §8).
- `docs/hospic-reference-analysis.md` (reference grammar + exclusions).
- `docs/hospic-to-care-clinic-implementation-plan.md` (page-by-page sequence).
- `docs/animation-reference-analysis.md` (motion patterns; per plan).
- `docs/frontend-design-exploration.md`, `docs/frontend-technology-and-skills-audit.md`
  (context; not re-read line-by-line this session).

---

## 4. Exact homepage files identified

| Role | File | Notes |
|------|------|-------|
| URL | `config/urls.py` (L5–8) → `website/urls.py` (L8) | `home` = name; included **un-namespaced** |
| View | `website/views.py` (`HomeView(TemplateView)`, L12–21) | context: `specialities`, `doctors`, `speciality_count`, `doctor_count` |
| Homepage template | `templates/home.html` (182 lines) | extends base; blocks `title`, `main_class="main--flush"`, `header_class=" site-header--hero"` |
| Base / shell | `templates/base.html` (139 lines) | skip-link, header/nav, main, footer, `app.js` |
| Header + nav | `templates/base.html` L16–70 | brand, `.nav-toggle`, `.site-nav`, role-aware links, POST logout |
| Hero | `templates/home.html` L8–44 + `styles.css` L581–697 | `.hero`, `.hero__grid/__copy/__lead/__actions/__panel`, `.hero-badge` |
| Hero illustration/decor | `styles.css` L594–624 (`.hero::before` texture, `.hero::after` dimensional layer) | inline SVG data-URIs; JS-off safe |
| About section | `templates/home.html` L67–116 + `styles.css` L1443–1497 | `.about-grid/__copy/__steps`, `figure.figure-plate`, `ol.about-steps` |
| Speciality section | `templates/home.html` L118–141 + partial + `styles.css` L1500–1547 | `.service-grid` + `partials/_speciality_card.html` |
| Doctor section | `templates/home.html` L143–166 + partial + `styles.css` L1550–1619 | `#doctors`, `.doctor-grid` + `partials/_doctor_card.html` |
| Statistics | `templates/home.html` L46–65 + `styles.css` L1419–1440 | `.band--compact` `.trust-strip/__item/__value/__label` |
| Closing CTA | `templates/home.html` L168–181 + `styles.css` L1622–1651 | `.cta-band`, `.cta-band__inner` |
| Footer | `templates/base.html` L92–134 + `styles.css` L1307–1365 | brand, Explore, Account, bottom bar |
| Shared partials | `templates/partials/_speciality_card.html`, `_doctor_card.html`, `_empty.html` | reused; **do not fork** |
| CSS | `static/css/styles.css` (1842 lines) | `:root` tokens L12–131; homepage rules above; responsive L1733–1818 |
| JS | `static/js/app.js` (170 lines) | nav toggle, autosubmit, confirm, guard, error-focus, one-shot reveals |

**Routes verified [observed]:** `home` (`/`), `speciality_list` (`/specialities/`),
`speciality_detail` (`/specialities/<slug>/`), `doctor_list` (`/doctors/`),
`doctor_detail` (`/doctors/<slug>/`); plus `admin/`, `accounts/`, `clinic/`,
`appointments/`, `dashboard/`. All resolved and rendered 200 in the baseline render.

---

## 5. Existing homepage section structure

Rendered `main > section` order at 1440 px **[observed]**:

| # | Element | id | `<h1/h2>` |
|---|---------|----|-----------|
| 1 | `section.hero` | — | `h1` "Care that fits your schedule." / `h2` "Find a doctor" (panel) |
| 2 | `section.band.band--compact.reveal` | — | *(no heading — aria-label "Clinic at a glance")* |
| 3 | `section.band.band--tint.reveal` | — | `h2#about-heading` "A simpler way to arrange your care" |
| 4 | `section.band.reveal` | — | `h2#services-heading` "Care across our clinical specialities" |
| 5 | `section.band.band--tint.reveal` | `doctors` | `h2#doctors-heading` "Meet the doctors accepting appointments" |
| 6 | `section.band.cta-band.reveal` | — | `h2#cta-heading` "Ready to book your visit?" |

**Heading outline [observed]:** exactly one `H1`; then `H2` ×5 (incl. hero panel) and
`H3` ×8 (5 specialities, 3 doctors). No skipped levels.

**Database vs hard-coded content [observed]:**
- **From DB:** speciality `name`/`description`/`get_absolute_url` (5 records);
  doctor name/speciality/qualification/`is_accepting_appointments`/`get_absolute_url`
  (3 records); `speciality_count` (5), `doctor_count` (3).
- **Hard-coded copy (static text, no invented claims):** hero badge/headline/lead,
  "Find a doctor" panel labels, About headings + 3-step list, section intros, CTA copy,
  footer tagline.
- **No** rating, price, testimonial, address, phone, hours or "years" data — **verified
  absent** in the rendered HTML **[observed]**.

---

## 6. Current design tokens and reusable components

**Tokens (`styles.css :root` L12–131) [observed]:**
- Palette: `--color-primary #0ea5a8`, `--color-primary-dark #0b7c80`,
  `--color-primary-darker #086063`, `--color-primary-soft #e8f8f8`, `--color-surface`,
  `--color-text #1f2937`, `--color-text-muted #6b7280`, `--color-border #e5e7eb`;
  ink scale `--ink-300…900`; brand scale `--brand-050…800`;
  surfaces `--paper #fff`, `--canvas #f7fafa`, `--canvas-2 #e8f8f8`, `--line`,
  `--line-strong`; semantic success/warning/danger/info.
- Type: `--font-sans`, `--font-serif` (system stacks), `--font-mono`;
  roles `--type-display-font`/`--type-page-font`/`--type-section-font` = serif,
  `--type-body-font`/`--type-support-font` = sans, `--type-data-font` = mono.
- Scale: `--text-display clamp(2.35rem…5rem)`, `--text-h2 clamp(1.75rem…2.6rem)`,
  `--text-h3 1.2rem`, `--text-lead 1.125rem`, `--text-body`, `--text-small`,
  `--text-caption`; leading `--leading-display 1.05`, `--leading-heading 1.18`,
  `--leading-body 1.65`; tracking `-0.02em`/`-0.015em`.
- Spacing `--sp-1…9`; radii `--radius-sm 8px`, `--radius 12px`, `--radius-lg 18px`,
  `--radius-pill 999px`; shadows `--shadow-sm/md/lg/card/card-hover`;
  layout `--container 1160px`, `--measure-heading 64ch`; motion tokens + focus ring.

**Reusable components [observed]:** `.btn` (+ `--primary/--secondary/--inverse/--lg/--sm/
--block/--arrow`, `.btn__disc`, `.btn__arrow`, `.link-button`); `.band`/`.band--tint`/
`.band--compact`; section-header grammar `.section-rule`/`.eyebrow`/`.section-title`/
`.section-intro`/`.band__head`/`.band__more`; `.trust-strip`; `.about-*`;
`.service-card` + `.doctor-card` (both flat, `border-radius: 0`, hairline-topped);
`.avatar`; `.cta-band`; `.empty`; `.reveal`; shared partials `_speciality_card`,
`_doctor_card`, `_empty`, `_field`, `_form_errors`.

---

## 7. Baseline observations at each viewport

Rendered with headless Chrome (system Chrome, `--headless=new`) against a **read-only**
snapshot produced by the Django test client (rolled-back transaction; `DB_ENGINE=sqlite`,
the documented local fallback). Data shown is the **live** `db.sqlite3` content
(5 specialities, 3 doctors). Full machine output: temp `…\phase-h1\report.json`.
**The dev server (`127.0.0.1:8017`) is not running; it was not started.**

| Metric | 390 px | 768 px | 1024 px | 1440 px |
|--------|--------|--------|---------|---------|
| Horizontal overflow | **0** | **0** | **0** | **0** |
| `<h1>` count | 1 | 1 | 1 | 1 |
| Console errors | 0 | 0 | 0 | 0 |
| Header | sticky, 63 px, white | sticky, 73 px, white | **absolute**, 73 px, transparent | **absolute**, 73 px, transparent |
| Nav toggle | flex, 44×88 px | flex, 44×88 px | **none** | **none** |
| `.site-nav` display | none (JS-off/closed) | none | flex | flex |
| Hero grid columns | 1 (359 px) | 1 (707 px) | 2 (467 / 423) | 2 (575 / 521) |
| Hero `h1` size / font | 37.6 px / serif | 54.4 px / serif | 67.2 px / serif | 80 px / serif |
| Hero gradient | yes (only gradient surface) | yes | yes | yes |
| `.hero::after` bg-size | 160 px (`opacity .78`) | 200 px | 245.76 px | 320 px |
| Figure-plate frame | 359×224 (ratio **1.60**) | 334×267 (**1.25**) | 445×356 (**1.25**) | 548×438 (**1.25**) |
| Trust strip | flex; "5 Active specialities", "3 Doctors accepting appointments"; `tabular-nums` | same | same | same |
| Band padding (compact / normal) | 32 / 60 px | 32 / 60 px | 35.84 / 71.68 px | 48 / 100.8 px |
| Section rule | 40×2 px | 40×2 | 40×2 | 40×2 |
| Service grid cols / cards | 1 / 5 | 2 / 5 | 2 / 5 | 3 / 5 |
| Doctor grid cols / cards | 1 / 3 | 2 / 3 | 2 / 3 | 3 / 3 |
| About grid cols | 1 (figure `order:-1`) | 2 | 2 | 2 |
| CTA band | **solid** `rgb(8,96,99)`, **no gradient** | same | same | same |
| Footer columns | 2 (Explore, Account) | 2 | 2 | 2 |

**Contrast (measured, solid backgrounds only) [observed]:**

| Element | Ratio | Size | Verdict |
|---------|-------|------|---------|
| `.section-title` (ink on tint) | 13.43 | 38.7–41.6 px | Pass |
| `.section-intro` (`#4b5563` on tint) | 6.91 | 18 px | Pass |
| `.about-copy p` / `.about-steps` | 6.91 / 6.91 | 18 / 16 px | Pass |
| `.trust-value` (`#0b7c80` on canvas) | 4.75 | 38–42 px | Pass |
| `.trust-label` (`#6b7280` on canvas) | 4.61 | 14.72 px | Pass (AA) |
| `.service-card__text` (`#6b7280`) | 4.61 | 15.2 px | Pass (AA) |
| `.eyebrow` (`#0b7c80` on tint) | 4.56 | 12.8 px | Pass (AA) |
| `.cta-band h2` (#fff on `#086063`) | 7.33 | 24–31.5 px | Pass |
| `.cta-band p` (`#e8f8f8` on `#086063`) | 6.71 | 16 px | Pass |
| **`.doctor-card__qual` (`#6b7280` on tint)** | **4.42** | **14.08 px** | **FAIL (AA, normal text)** |
| `.hero__lead` (white .92 on gradient) | n/a | 18 px | Not computable (gradient) |

**Nav role states [observed]:** anonymous → Specialities, Doctors; account → Log in,
Register, Book appointment. Patient → Specialities, Doctors, Dashboard, My appointments;
account → Book appointment, Log out (POST form). No `aria-current` on `/` (expected).

**Screenshots captured (not visually inspected — see §11):**
`…\phase-h1\shots\home_anon_390.png` (34,115 B), `home_anon_1440.png` (54,411 B).

---

## 8. Current visual gaps

Observed facts vs the plan/reference. "Later phase" = the plan's H2–H6 (§9 of the plan).

| # | Current behaviour | File responsible | What needs improvement | Why it matters | Owned by | Regression risk | How to validate later |
|---|-------------------|------------------|------------------------|----------------|----------|-----------------|------------------------|
| **G1** | About band header (rule + eyebrow + `h2` + intro) is written directly inside `.about-copy`; it is **not** wrapped in the shared `.band__head` used by the Services/Doctors bands (`bandHeadCount=2`, not 3) | `templates/home.html` L67–96; `styles.css` `.about-copy` L1449, `.band__head` L1415 | Make the About header use the same `.band__head` grammar/measure so the three labelled bands read identically | Header grammar is the page's spine; inconsistent wrappers cause subtly different measures/spacing | **Plan H1 (originally)** — deferred here | Touch about-band markup only; keep `#about-heading`, steps, figure | Re-render at 4 widths; confirm `.band__head` count = 3, one `h1`, `#about-heading` present |
| **G2** | **Plan assumption corrected:** `.cta-band` is **already flat** (solid `#086063`, `background-image: none`, good contrast 7.33/6.71) | `styles.css` L1622–1646 | The plan's "flatten the CTA gradient" task is largely **already satisfied**; re-scope H2 to minor polish or drop it | Avoids wasted work / needless churn on a band that already meets the intent | Plan H2 (re-scope) | Low | Computed `background-image:none` + contrast ≥ AA at 4 widths |
| **G3** | `.doctor-card__qual` renders `#6b7280` on the tint band at **4.42:1** (14.08 px) — **below AA 4.5** | `styles.css` L1597; `partials/_doctor_card.html` L14 | Raise contrast (e.g. `#4b5563` as used elsewhere on tint) | Accessibility: small meta text fails WCAG AA | Plan H5 (contrast) / H3 | Shared partial + colour change touches doctor cards on 3 pages | Recompute contrast ≥ 4.5 at 4 widths; website tests still pass |
| **G4** | Figure-plate aspect ratio differs: **1.60** at 390 px vs **1.25** at ≥768 px (full-width on mobile makes it comparatively taller) | `styles.css` `.figure-plate` L1453; media `(max-width:760px)` L1799 | Consider a consistent `aspect-ratio` frame across widths | Visual consistency of the "journal plate"; avoids layout jump | Plan H3 | Decorative block only; caption/`aria-hidden` unaffected | Computed frame ratios at 4 widths |
| **G5** | `.eyebrow` (tracked ALL-CAPS label) is still present (3 instances) | `templates/home.html`; `styles.css` L1392 | Decision needed: keep or remove (broader 7.5 plan Phase 2 slated removal; spec §D4 left it open) | Affects editorial tone; must not remove meaning | **Unresolved (spec D4)** — not in H2–H6 | Low (decorative label) | Visual + no-dependency check; decide before implementing |
| **G6** | `.service-card`/`.doctor-card` have `border-radius: 0` (flat), with hairline tops | `styles.css` L1508/1558 | Not a defect — consistent with editorial direction; confirm against spec radius direction (D8) | Determines overall "flat vs rounded" feel | Decision D8 | Low | Visual check at 4 widths |
| **G7** | Hero is the **only** gradient surface; one dimensional pseudo-element (`::after`) present and scaled 160→320 px | `styles.css` L581–624 | No change needed; **guard** against adding a second dimensional/gradient element | Preserves the single "bold moment" rule | Guard (all phases) | — | Count gradient surfaces after each change |
| **G8** | Trust strip already real-count-only with `font-variant-numeric: tabular-nums` | `templates/home.html` L46–65; `styles.css` L1433 | Plan's tabular-nums action is **already satisfied** | Avoids redundant work | Plan H3 (re-scope) | Low | Computed `font-variant-numeric` |

**No invented content observed:** no rating, review, price, testimonial, address, phone,
hours, "years"/patient counts, or medical claims in the rendered homepage **[observed]**.

---

## 9. File-by-file recommendations for later phases

Recommendations only — **nothing implemented** in H1. Mapping to the plan's H2–H6
(§8/§9 of the plan), with the corrections noted in §8.

| Rec | File(s) | Change (proposed) | Plan phase | Notes |
|-----|---------|-------------------|------------|-------|
| R1 | `templates/home.html` (About L67–96), `static/css/styles.css` | Wrap the About header in the shared `.band__head` grammar (the plan's *original* H1 change) | plan-H1 → fold into H4 or a revised H1 | Keep `#about-heading`, steps, figure |
| R2 | `static/css/styles.css` (`.cta-band` L1622–1646) | **Re-scope**: band is already flat — keep; only micro-polish if needed | plan-H2 (re-scope) | Do not add a gradient |
| R3 | `static/css/styles.css` (`.doctor-card__qual` L1597) | Fix contrast `#6b7280`→`#4b5563` on tint (≥4.5:1) | plan-H5 | Shared card affects home + listings |
| R4 | `static/css/styles.css` (`.figure-plate` L1453; media L1799) | Normalise figure-plate `aspect-ratio` across widths | plan-H3 | Decorative; caption/`aria-hidden` intact |
| R5 | `static/css/styles.css` (`.trust-value` L1433) | Already `tabular-nums` — **no action** | plan-H3 (verify) | Confirm only |
| R6 | `templates/home.html` / `static/css/styles.css` (`.eyebrow` L1392) | Decide keep vs remove | unresolved (D4) | Needs a decision before coding |
| R7 | `website/tests.py` | Add homepage contract assertions (200, active speciality rendered, one `h1`, `#doctors` anchor, `doctor_list` CTA, `accounts:register` anon-only, trust strip conditional) | plan-H6 | Additive only |
| R8 | `docs/` | Per-phase reports | plan-H6 | Follow existing report pattern |

**Untouched / confirmed reusable:** `templates/base.html`, `static/js/app.js`,
`templates/partials/*` (except the card-colour change in R3), `website/views.py`,
`config/urls.py`, `website/urls.py` — all verified working and within contract.

---

## 10. Validation commands and actual results

Environment: project venv `C:\venvs\anmaya-clinic\Scripts\python.exe` (Python 3.12),
settings `config.settings.development`, `DB_ENGINE=sqlite` (documented local fallback).

| Command | Result | Exit |
|---------|--------|------|
| `python manage.py check` | `System check identified no issues (0 silenced).` | 0 |
| `python manage.py makemigrations --check --dry-run` | `No changes detected` | 0 |
| `git diff --check` | clean — only benign `LF will be replaced by CRLF` warnings (pre-existing) | 0 |

**Not run (intentionally):** the full `manage.py test` / `pytest` suites — the H1 task and
plan do not require them here, and no code changed. They must be run at the end of each
**implementation** phase (plan §9.2).

---

## 11. Limitations and unverified assumptions

1. **No image input:** screenshots were captured but **not visually inspected**. All
   "baseline observations" are **computed geometry/styles + rendered-HTML** measurements,
   not perceptual review. No screenshot critique is claimed.
2. **Dev server not running and not started** (`127.0.0.1:8017`): the baseline was rendered
   via the Django test client into a temp HTML snapshot (static paths rewritten to
   `file://`), inside a **rolled-back transaction** (no data persisted). This exercises the
   real templates/CSS/JS in headless Chrome, but is not a live-server session.
3. **Gradient contrast not computable:** the hero uses a gradient, so `.hero__lead`
   contrast is unmeasured (reported as `n/a`). Only solid-background pairs were measured.
4. **Pseudo-element styles limited:** `.hero::before/::after` were read via
   `getComputedStyle(el, ':after')` (background-size/opacity only).
5. **MySQL/InnoDB unverified** (ADR-003): suite/render run on SQLite fallback.
6. **Cross-platform fonts unverified:** serif rendering measured on Windows Chrome only.
7. **Assumptions carried, not confirmed:** the plan's claim that `.cta-band` carried a
   gradient is **incorrect for the current build** (G2); the `.trust-value` tabular-nums
   action is already satisfied (G8). Both are recorded as corrections, not as work.
8. Baseline reflects the **current live `db.sqlite3`** (5 specialities / 3 doctors); a
   different dataset would change card counts (not layout).

---

## 12. Git status after inspection

Re-verified after writing this report. The tracked-file diff set is **unchanged** from §2
(the same 40 modified files), and **nothing is staged**. The **only** new file is this
report, `docs/homepage-h1-baseline-report.md` (untracked, documentation only). No other
repository change was made.

_(Baseline scratch artefacts — `render.py`, `qa.mjs`, `summarize.py`, `report.json`,
`html/`, `shots/` — live under `…\Temp\opencode\phase-h1\`, **outside** the repository.)_

---

## 13. Confirmation that no application code was changed

**Confirmed.** No application code, template, stylesheet, script, test, setting, model,
migration, URL, or dependency was created, edited, or deleted during H1. The only file
written **inside the repository** is this report. Nothing was staged, committed, or
pushed; no destructive Git command (reset/checkout-discard/clean/stash) was used; all
pre-existing uncommitted work was preserved.

---

## 14. Confirmation that H2 was not started

**Confirmed.** H2 (and H3–H6) were **not** started. No homepage template or CSS change was
made. This report is the sole H1 deliverable; work stops here pending human review.
