# Hospic → Care_Clinic Implementation Plan

> How the transferable grammar from the **Hospic** reference
> (`docs/hospic-reference-analysis.md`) is applied to Care_Clinic, page by page, in
> bounded stages, without breaking the approved architecture, contracts or existing
> work. This document *extends* `docs/phase-7.5-implementation-plan.md`; it does not
> replace it.

---

## 1. Baseline (state before this plan)

**Verified baseline**

- Phases 0–7.4.2 complete: `manage.py check` clean; no pending migrations;
  `manage.py test` **205 OK (skipped=1)**; `pytest` **204 passed, 1 skipped**;
  `git diff --check` clean (CRLF only).
- Phase 7.5 executed so far against the 14-phase plan:
  - **Plan P1** (typography tokens + serif display) — done.
  - **Plan P2** (editorial labels + heading measures) — done.
  - **Plan P4** (homepage hero) — CSS applied; **report not yet written**.
  - **Plan P3** (shared editorial cards) — **not** done (deliberately skipped).
- Only app file changed across P1–P4: `static/css/styles.css` (now **1784 lines**).
- Architecture: server-rendered **Django templates**, hand-built **CSS** (ADR-020),
  one optional `static/js/app.js` (progressive enhancement), **no build step, no CDN,
  no web fonts**, usable with JS off.
- Dev server: `127.0.0.1:8017` (`config.settings.development`).

**Contracts that must not change** (spec §K): URL names, context variable names, form
field names, security/permission behaviour, and the test-asserted template strings in
§K.5 (e.g. home must render an active speciality's name; the register page keeps
"patients only").

---

## 2. Relevant patterns from the reference

Adopted **only** as grammar (analysis §2.2): a single reusable section-header block; a
short rule above the section label; a captioned figure plate; large tabular numerals
for **real** counts; a genuine ordered list for process content; bands separated by
rules + spacing. Everything else in Hospic is excluded (§9).

---

## 3. Preserved decisions (unchanged)

- **ADR-020** — hand-built CSS, no framework, no build step, no CDN, no web fonts,
  single optional `app.js`, JS-off usable. *This takes precedence over the "Bootstrap 5"
  wording in the integration task prompt (open conflict — see analysis §7.1).*
- **Palette** — `#0EA5A8`, `#0B7C80`, `#E8F8F8`, `#FFFFFF`, `#1F2937`, `#6B7280`,
  `#E5E7EB`.
- **Concept** — A (Editorial Clinical) identity + C (Modern Medical Journal) layout
  grammar + exactly **one** dimensional hero element (`.hero::after`, already built).
- **Type** — serif display on `h1`/`h2` only; sans UI/body; mono/sans numerals.
- **Motion** — opacity/transform only, one-shot reveals via `IntersectionObserver`,
  fully neutralised under `prefers-reduced-motion`; complete with JS off.
- **Content rule** — real data only; no invented statistics, claims, quotes or media.

---

## 4. Page-by-page sequence

Sequenced by value and risk; each row is one **bounded stage**. Home is worked first
because the phase-7.5 plan already begins there and the hero is complete.

| Order | Stage | Surface | Reference device applied |
|-------|-------|---------|--------------------------|
| 5 | **Home bands & editorial components** ← *this stage* | `templates/home.html`, `static/css/styles.css` | Section-header grammar (rule + label + serif H2), captioned figure plate, tabular real counts, honest ordered list, rule-separated bands, flat closing CTA |
| 3* | Shared editorial cards | `partials/_speciality_card.html`, `partials/_doctor_card.html`, CSS | Hairline-separated editorial entries; drop gradient avatar/washes |
| 6 | Specialities pages | `speciality_list.html`, `speciality_detail.html`, CSS | Reuse band/section grammar |
| 7 | Doctors + doctor detail | `doctor_list.html`, `doctor_detail.html`, CSS | Reuse entries + figure plate |
| 8 | Accounts (auth) | `accounts/*.html`, CSS | Consistent auth panel on the section grammar |
| 9 | Appointments + dashboards | `appointments/*.html`, `dashboards/*.html`, CSS | Consistent tables/cards |
| 10 | Footer + global chrome | `templates/base.html`, CSS | Expanded footer, real links only |
| — | Homepage-hero report (backfill) | `docs/` | Write the missing P4 deliverable |

\* *Stage 3 is plan-P3, currently skipped; scheduled here because the home cards inherit
from it. Not part of this stage.*

---

## 5. Component / CSS / JS scope per stage

### 5.1 This stage (Stage 5 — Home bands)

**Template `templates/home.html`**
- Add a decorative short rule (`<span class="section-rule" aria-hidden="true">`) as the
  structural lead-in of the three labelled bands (About, Specialities, Doctors).
- Convert `.about-visual` (a gradient block) into a **figure plate**: a `<figure>` with
  the existing decorative SVG (`aria-hidden`) plus an honest `<figcaption>`.
- No change to ids, `aria-labelledby`, loops, context variables or CTA destinations.

**CSS `static/css/styles.css`**
- New primitives: `.section-rule`; `.figure-plate` + `.figure-plate__caption`.
- Refine existing (replace, don't duplicate): `.band` / `.band--*`, `.band__head`,
  `.about-*` (incl. flat figure plate replacing the gradient), `.trust-strip` /
  `.trust-value` / `.trust-label`, `.about-steps`, `.cta-band` (flat, no gradient).
- Reuse tokens only. No new colour, font or motion tokens.

**JS `static/js/app.js`** — **no change** (no new behaviour; reveals already exist).

**Boundedness** — this stage does **not** touch shared card partials, the hero, the
header/footer, or any non-home page. One bounded stage, then stop.

### 5.2 Later stages (scope sketch)

- **Stage 3 (cards):** edit the two partials + card CSS; remove gradient avatar; keep
  markup hooks. Then **Stage 6/7** reuse the same grammar on the listing/detail pages.
- **Stages 8–10:** apply the same section grammar to auth/appointments/dashboards and
  expand the footer with real URL names only.

---

## 6. Responsive & accessibility (every stage)

- Test at **390 / 768 / 1024 / 1440** px. No horizontal overflow at any width.
- Exactly one `h1` per page; heading order preserved.
- Contrast ≥ WCAG AA for all text (muted grey darkened one step on teal tint bands).
- All decorative motifs `aria-hidden`; figure captions are real text.
- **Reduced motion:** every new transition/animation gated by the existing
  `prefers-reduced-motion` block.
- **JS off:** `no-js` state shows all content (no content hidden behind `.reveal`).
- Interactive targets ≥ 44 px; visible `:focus-visible` on chips, buttons and rules.
- Touch: any hover affordance has a non-hover equivalent (border/underline).

---

## 7. Verification (per stage)

**Automated (must pass before reporting):**

1. `python manage.py check`
2. `python manage.py makemigrations --check --dry-run` → "No changes detected"
3. `python manage.py test` (large timeout)
4. `pytest -q`
5. `git diff --check` → clean (CRLF only)
6. CSS brace balance + template count sanity.

**Browser (headless Chrome via `playwright-core`, server `127.0.0.1:8017`):** for each
of the 6 main pages × 4 widths — `scrollWidth ≤ clientWidth` (no overflow), one `h1`,
no console errors, low-contrast text list empty; plus a **reduced-motion** pass and a
**no-JS** pass on `/`. Confirm nav, hero CTA and closing CTA targets.

**Tooling constraint:** the assistant cannot inspect images, so the *perceptual*
screenshot critique cannot be performed; only quantitative results are reported, and no
screenshot inspection is claimed unless screenshots were actually captured and reviewed.

---

## 8. Dependencies & risks

| Risk | Mitigation |
|------|-----------|
| Bootstrap-5 instruction vs ADR-020 | Follow ADR-020; record the conflict; ask the user to confirm |
| No licensed photography | Figure plate is a flat decorative motif + honest caption |
| Removing gradients could read "plain" | Keep the one dimensional hero moment; rules/space carry the rhythm |
| Touching shared partials breaks other pages | Shared cards are **out of scope** this stage |
| Long test runtime vs shell timeout | Run with an explicit large timeout |
| Preserving uncommitted work | No `git reset/checkout/clean`; edits only; rollback rule honoured |

---

## 9. Explicit exclusions

- **No** React / Next.js / Framer runtime; **no** Lenis, GSAP, Three.js; **no** new build
  system, **no** new package, **no** CDN, **no** web fonts.
- **No** copy of any Hospic asset, font, image, video, SVG file or copy.
- **No** invented data: rating badge, packages/pricing, testimonials, blog, FAQ,
  opening hours, address, phone, email, social links, "years of excellence", patient
  counts, satisfaction — all omitted.
- **No** changes to models, migrations, permissions, URL names, booking services, form
  field names or auth behaviour.
- **No** second dimensional element beyond the existing hero plate.
- **No** commit / push; no destructive git; do not auto-advance to the next stage.

---

## 10. Per-stage acceptance criteria

**Stage 5 — Home bands (this stage):**
- [ ] Home returns 200; active speciality name still rendered (K.5).
- [ ] Section-header grammar (rule + label + serif H2 + lede) consistent across the
      three labelled bands; exactly one `h1` on the page.
- [ ] About figure plate is flat (no gradient), decorative SVG `aria-hidden`, caption
      is real text; no fake image.
- [ ] Trust strip shows only real counts; numbers tabular; no invented metric.
- [ ] Closing CTA band flat (no gradient), same destinations as before
      (`doctor_list`, and `accounts:register` when anonymous).
- [ ] `check` / `makemigrations --check` / `manage.py test` / `pytest` / `git diff --check`
      all pass; no overflow, no console errors, no low-contrast text at 390/768/1024/1440;
      reduced-motion and no-JS passes OK.
- [ ] Implementation report written; work stopped for review.

*(Later stages carry the same acceptance skeleton, applied to their own surfaces.)*
