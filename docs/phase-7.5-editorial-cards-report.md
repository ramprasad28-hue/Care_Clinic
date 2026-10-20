# Phase 7.5 — Phase 3 (Shared Editorial Cards) — Report

> **Date:** 2026-10-18
> **Project:** `C:\Users\Ramprasad\OneDrive\Desktop\Care_Clinic`
> **Phase:** 7.5 / Phase 3 — transform the shared speciality and doctor cards into premium
> editorial entries.
> **Application files changed:** `static/css/styles.css`, `templates/partials/_speciality_card.html`,
> `templates/partials/_doctor_card.html`.
> **Deliverable:** this report (`docs/phase-7.5-editorial-cards-report.md`).
> **Nothing committed or pushed.** No Phase 6 or later work started. No backend, model, view, form,
> URL, migration, setting, dependency or JavaScript file was changed.
> **Skills applied:** `design-taste-frontend` (project-local, `.agents/skills/design-taste-frontend`),
> read for the house rules that apply to a component; `frontend-design`, `web-design-guidelines`
> (used in earlier 7.5 phases).

---

## 1. Files changed

| File | Change |
|---|---|
| `static/css/styles.css` | `.service-grid`, `.service-card*`, `.doctor-grid`, `.doctor-card*`, `.avatar` refactored **in place** (lines ~1487–1615). Removed the `.service-card__icon` rules and the `.doctor-card .btn` rule; added `.doctor-card__link`. |
| `templates/partials/_speciality_card.html` | Decorative icon tile removed; card is now a title-first editorial index entry. |
| `templates/partials/_doctor_card.html` | Trailing `.btn` replaced with an editorial text link (`doctor-card__link`). |
| `docs/phase-7.5-editorial-cards-report.md` | This report (new). |

No parent template was modified. Every page that includes the partials picks the change up unchanged:
`templates/home.html` (both), `website/templates/website/speciality_list.html`,
`website/templates/website/doctor_list.html`, `website/templates/website/speciality_detail.html`.

---

## 2. Design direction applied

**Premium editorial.** The cards stop being SaaS panels (rounded surface, drop shadow, hover
lift, coloured icon tile, gradient avatar) and become restrained index entries: a single hairline
top rule, a title in the existing heading hierarchy, a concise description, and an understated
arrow/text call to action. Existing design tokens and typography remain authoritative.

**Typography note (deliberate).** The Phase 3 plan text and the approved exploration mention a
*serif* entry title. Phase 1 (`docs/phase-7.5-typography-report.md` §2) fixed serif to the display
levels only — `h1`/`h2` — and explicitly listed `.service-card__title` / `.doctor-card__name` as
staying on the system sans. To keep the established typography authoritative, the card titles stay
**sans**; the editorial feel is carried by structure (rules, spacing, restraint) rather than a new
font role. This is recorded as a deliberate deferral, not an oversight.

---

## 3. Speciality entry (`_speciality_card.html`)

- Removed `span.service-card__icon` (purely decorative `aria-hidden` glyph — an "icon-topped
  feature card" tell) and its CSS.
- Structure is now: `<h3 class="service-card__title"><a…>` → optional `p.service-card__text`
  (still `{{ speciality.description|truncatewords:18 }}`) → `a.service-card__link` "View doctors" + arrow.
- No wrapper is clickable; the title link and the explicit CTA link are the only interactive
  elements, so there are no nested interactive links.
- The thumbnail-less, rule-first layout is shared by the homepage specialities band and
  `/specialities/`.

## 4. Doctor entry (`_doctor_card.html`)

- Kept: initial-based monogram avatar (no photo, no invented data — ADR-015), `<h3>` name link,
  speciality line, and the real `doctor-card__meta` list (qualification, "Accepting appointments").
- Changed: the trailing `<a class="btn btn--secondary btn--sm">` became
  `<a class="doctor-card__link">` (same destination and label, "View profile & book"), so the
  doctor entry visually complements the speciality entry.
- No new fields, queries or placeholder content were introduced.

---

## 4. CSS refactor (in place)

| Selector | Before | After |
|---|---|---|
| `.service-grid` / `.doctor-grid` | `gap: var(--sp-5)`; `minmax(300px/320px, 1fr)` | `gap: var(--sp-6) var(--sp-7)`; both `minmax(300px, 1fr)` |
| `.service-card` / `.doctor-card` | `background`, `border: 1px solid`, `border-radius`, `padding`, `box-shadow: var(--shadow-card)`, transform+shadow `transition` | transparent; `border-top: 1px solid var(--line)`; `padding-top: var(--sp-4)`; `transition: border-color …` only |
| `:hover, :focus-within` | `translateY(-hover-lift)` + `shadow-card-hover` + border colour | `border-top-color: var(--brand-600)`; the title link also underlines (non-colour cue) |
| `.service-card__icon` | 3rem tinted rounded tile | removed |
| `.avatar` | `linear-gradient(135deg, brand-600, brand-700)`, `border-radius: 999px`, inflating shadow-free but gradient | flat `background: var(--paper)`, `border: 1px solid var(--brand-200)`, `color: var(--brand-700)`, `border-radius: var(--radius-sm)`, 3rem |
| `_link` (both) | service only, `:hover` underline | shared hover/focus-visible underline; both entries use it |
| `.doctor-card .btn` | left-aligned auto-margin button | removed; replaced by `.doctor-card__link` |

`--shadow-card` / `--shadow-card-hover` / `--hover-lift` are no longer referenced by these cards.
They are **left defined** (token-system stability) rather than deleted; no unrelated rule was
touched.

---

## 4a. Taste-skill house rules — applied vs not applied

| Rule | Applied? | Note |
|---|---|---|
| No gradients | Yes | avatar gradient removed. |
| No shadows on things at rest | Yes | card `box-shadow` removed (`box-shadow: none` measured). |
| No icon-topped feature cards | Yes | icon tile removed. |
| No exaggerated radii | Yes | card radius removed; avatar `999px` → `8px`. |
| No hover lift | Yes | `translateY` removed; hover is a border-rule colour + underline. |
| No colour-alone state | Yes | hover/focus also underlines the title and the CTA. |
| No thin rules / no hairline dividers | **No — deliberate.** | The approved editorial direction (`docs/frontend-design-exploration.md`) mandates hairline rules as the primary structural device. Project direction overrides the skill here. |
| No rows of identical cards | **No — deliberate.** | Specialities and doctors are inherently parallel lists; the entry pattern is the approved treatment. |

---

## 4. Compatibility preserved

- `{% if speciality.description %}`, `{% if doctor.qualification %}`,
  `{% if doctor.is_accepting_appointments %}` conditionals kept.
- Links unchanged: speciality → `speciality.get_absolute_url`; doctor → `doctor.get_absolute_url`.
- No RBAC, permission, view or context change; the partials are still plain `{% include %}`s.
- Test strings intact: "Cardiology" present / "Dermatology" present in the seeded set,
  "Alice Anderson" / "Bob Brown" visibility, doctor detail "Monday" and "15 min" all covered by the
  suites below, which pass.

---

## 5. Validation

| Command | Result |
|---|---|
| `python manage.py check` | `System check identified no issues (0 silenced).` |
| `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| `python manage.py test` | **OK**, 205 tests, `skipped=1` |
| `pytest -q` | **204 passed**, 1 skipped (284.64s) |
| `git diff --check` | exit 0 (only pre-existing `core.autocrlf` LF→CRLF advisories) |

Environment: `C:\venvs\anmaya-clinic\Scripts\python.exe` (Python 3.12), Django dev settings.

---

## 6. Browser verification

Tooling: the repository's own browser tooling — the `design-taste-frontend` CDP driver
(`.agents/skills/design-taste-frontend/scripts/lib/cdp.mjs`) driving installed Chrome
(`C:\Program Files\Google\Chrome\Application\chrome.exe`, Node v22.23.1). Live dev server on
`http://127.0.0.1:8017/` (restarted once — see §7). Screenshots: `.taste-skill/inspect/phase3/`.

Pages: `/`, `/specialities/`, `/doctors/`, `/specialities/cardiology/`.

| Check | Result |
|---|---|
| Horizontal overflow (`scrollWidth − clientWidth`) | **0 px** at 390 / 768 / 1024 / 1440 on every page |
| Columns — `.service-grid` / `.doctor-grid` | 390 → **1**; 768 → **2**; 1024 → **2**; 1440 → **3** |
| Titles & text rendered | cards visible, every card has an `h3` title and (specialities) description |
| Link destinations | resolve to `/specialities/<slug>/` and `/doctors/<slug>/` |
| Card surface at rest | `border-top: 1px rgb(229,231,235)`, `box-shadow: none`, `background: transparent`, `border-radius: 0` |
| Hover | top rule `rgb(229,231,235)` → `rgb(14,165,168)` (= `--brand-600`) on `/specialities/`, `/doctors/`, `/specialities/cardiology/` (the two homepage probes missed the off-screen card — a test-coordinate artefact, not a CSS failure) |
| Keyboard focus | tabbed to a card link → `outline: 3px solid rgb(11,124,128)` visible |
| `prefers-reduced-motion: reduce` | media matches; card `transition-duration` collapses to `1e-06s` |
| JavaScript disabled | all cards render with correct columns (`Emulation.setScriptExecutionDisabled`) |

**Perceptual review limitation.** The screenshots were captured as required, but the model
answering this task **cannot read image input**, so no visual/perceptual judgement of the
screenshots was performed. All findings above are quantitative measurements from the DOM/CSSOM.
This is stated explicitly rather than claiming a visual review that did not happen.

---

## 7. Dev-server note

The server listening on `:8017` was serving **stale templates** (the removed `service-card__icon`
was still present, the new `doctor-card__link` absent) while serving fresh static CSS. Cause:
`manage.py runserver --noreload` plus Django ≥ 4.1's default cached template loader, which is not
invalidated without the autoreloader. Two duplicate project runservers were present; both were
stopped and a single fresh `runserver 127.0.0.1:8017` on the project venv was started. Served HTML
then matched the files. No unrelated process was touched.

---

## 8. Deliberate divergences / follow-ups

1. **Card titles remain sans** (see §2) — the serif-entry-title idea from the plan is deferred to a
   future typography decision.
2. **Hairline top rules retained** against the skill's "no thin rules" rule — mandated by the
   approved editorial direction.
3. **`--shadow-card`, `--shadow-card-hover`, `--hover-lift` are now unused by cards** but kept in
   the token layer to avoid design-system churn. A later cleanup phase may remove them.
4. `templates/partials/` is currently **untracked** in git; these files will appear as new files on
   the next `git add`.

---

## 9. Git status

`git status --short` inspected; no staging, commit, branch or push was performed. All pre-existing
uncommitted work is preserved. The only tracked file changed by this phase is
`static/css/styles.css` (which already carried a large uncommitted 7.5 refactor — `HEAD` version is
321 lines vs. the ~1819-line working file).
