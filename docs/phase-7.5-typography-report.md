# Phase 7.5 — Phase 1 (Editorial Typography Tokens) — Report

> **Date:** 2026-10-17
> **Project:** `C:\Users\Ramprasad\OneDrive\Desktop\Care_Clinic`
> **Phase:** 7.5 / Phase 1 — introduce a refined editorial typography system.
> **Application file changed:** `static/css/styles.css` **only**.
> **Deliverable:** this report (`docs/phase-7.5-typography-report.md`).
> **Nothing committed or pushed.** No Phase 2 or later work was started.
> **Skills applied:** `frontend-design`, `web-design-guidelines` (guidelines fetched from
> `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`).

---

## 1. Files changed

| File | Change |
|---|---|
| `static/css/styles.css` | Typography token layer added; heading/body/data consumers re-pointed to the new semantic tokens. **Only** `font-family` declarations and token definitions changed — no layout, spacing, colour, radius, shadow, motion or responsive rules were touched. |
| `docs/phase-7.5-typography-report.md` | This report (new). |

No template, JavaScript, view, model, form, URL, migration, setting, or dependency was changed.

---

## 2. Design decision — conservative serif

The approved direction (hybrid, `docs/frontend-design-exploration.md` §3.2/§5.2) calls for a
system-serif display face while ADR-020 forbids web fonts. The rule implemented:

> **Serif is applied to the two *display levels* only — the page heading (`h1`) and the section
> heading (`h2`).** Subheads (`h3`/`h4`), all UI, labels, body copy and every numeral stay on the
> existing system sans; identifiers stay on mono.

This satisfies rule 3 ("introduce the serif conservatively — do not force every heading or
component to use serif"): the serif is a *display/page/section* voice, not a global swap, and it
avoids a real defect — system serifs like Georgia use **old-style (non-lining) figures**, so
numerals (`.stat-value`, `.trust-value`, `.step::before` counters, `.ticket__date`) were
deliberately left on the sans stack to keep tabular/stat figures consistent.

---

## 3. Typography tokens introduced or adjusted

### New tokens

| Token | Value | Purpose |
|---|---|---|
| `--font-sans` | `system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` | Canonical system sans (single source of truth; previously duplicated across `--font-display`/`--font-body`). |
| `--font-serif` | `ui-serif, "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, "Times New Roman", "Liberation Serif", serif` | Editorial display/heading serif. |
| `--font-data` | `var(--font-mono)` | Semantic alias for the existing mono stack. |
| `--type-display-font` | `var(--font-serif)` | Hero `h1` (display role). |
| `--type-page-font` | `var(--font-serif)` | Page heading (`h1`). |
| `--type-section-font` | `var(--font-serif)` | Section heading (`h2`). |
| `--type-body-font` | `var(--font-sans)` | Body copy. |
| `--type-support-font` | `var(--font-sans)` | Supporting text (section intros, `.muted`). |
| `--type-data-font` | `var(--font-data)` | Identifiers — appointment reference, table reference cell. |

### Adjusted (same value, single source)

| Token | Before | After | Note |
|---|---|---|---|
| `--font-display` | inline sans stack | `var(--font-sans)` | Identical computed value; no visual change. |
| `--font-body` | inline sans stack | `var(--font-sans)` | Identical computed value; no visual change. |

### Preserved untouched

`--font-mono`, and the entire size/leading/tracking scale: `--text-display`, `--text-h2`,
`--text-h3`, `--text-lead`, `--text-body`, `--text-small`, `--text-caption`, `--leading-display`,
`--leading-heading`, `--leading-body`, `--tracking-display`, `--tracking-heading`. No size, weight,
line-height or tracking value was changed (rule 4 & 7).

---

## 4. Font stacks used

- **Serif (display/page/section):** `ui-serif, "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, "Times New Roman", "Liberation Serif", serif`
- **Sans (UI, body, numerals):** `system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`
- **Mono (identifiers):** `"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace`

All are **system** stacks — no download, no `@font-face`, no CDN, no new dependency (ADR-020).

---

## 5. Consumers changed (exact rules)

| Selector | Before | After |
|---|---|---|
| `body` | `var(--font-body)` | `var(--type-body-font)` (sans — identical) |
| `h1` | (group) `var(--font-display)` | `var(--type-page-font)` → **serif** |
| `h2` | (group) `var(--font-display)` | `var(--type-section-font)` → **serif** |
| `.hero h1` | (inherited from `h1`) | `var(--type-display-font)` → serif (explicit display role) |
| `.section-title` | (inherited from `h2`) | `var(--type-section-font)` → serif (explicit) |
| `.section-intro` | (inherited sans) | `var(--type-support-font)` (sans — explicit role) |
| `.muted` | (inherited sans) | `var(--type-support-font)` (sans — explicit role) |
| `.data-table .cell-ref` | `var(--font-mono)` | `var(--type-data-font)` (mono — identical) |
| `.ticket__ref` | `var(--font-mono)` | `var(--type-data-font)` (mono — identical) |

The heading group (`h1, h2, h3, h4`) retains `font-family: var(--font-display)` as the **sans
base**; `h1`/`h2` override immediately to the serif role tokens. `h3`, `h4`, and all component
headings (`.service-card__title`, `.doctor-card__name`, `.filters legend`, `.empty h2/h3`,
`.site-footer__heading`, `.stat-value`, `.brand`, `.ticket__date`) remain on the sans stack.

Also updated: the file-header comment block (line 6) which previously read "a single system sans
for both display and UI".

---

## 6. Viewport measurements (headless Chrome, system Chrome binary)

Measurements at **390 / 768 / 1024 / 1440 px**; 6 public/unauthenticated pages
(`/`, `/specialities/`, `/doctors/`, `/accounts/login/`, `/specialities/cardiology/`,
`/doctors/aswin-kumar/`) × 4 widths = **24 page-width combinations**, all with **no horizontal
overflow**.

### Hero `h1` (home — "Care that fits your schedule.")

| Width | Size | Lines | Box (w×h) | Letter-spacing | Computed family |
|---|---|---|---|---|---|
| 390 | 38 px | 2 | 359×79 | −0.752 px | `ui-serif` |
| 768 | 54 px | 1 | 707×57 | −1.088 px | `ui-serif` |
| 1024 | 67 px | 2 | 468×141 | −1.344 px | `ui-serif` |
| 1440 | 80 px | 2 | 575×168 | −1.6 px | `ui-serif` |

Box height equals `lines × line-height` at every width → **no clipping or overlap**. The two-line
wrap at 1024/1440 is the pre-existing two-column hero grid constraining `h1` width; unchanged by
this phase.

### Section titles (home `.section-title` × 3)

| Width | Size | Lines |
|---|---|---|
| 390 | 28 px | 2 each |
| 768 | 34 px | 1–2 |
| 1024 | 39 px | 2 each |
| 1440 | 42 px | 2 each |

### Page `h1` (listings / detail / login)

| Width | `/specialities/` | `/doctors/` | `/accounts/login/` | Family |
|---|---|---|---|---|
| 390 | 30 px, 1 line | 30 px | 30 px | `ui-serif` |
| 768 | 39 px, 1 line | 39 px | 39 px | `ui-serif` |
| 1024 | 45 px, 1 line | 45 px | 45 px | `ui-serif` |
| 1440 | 46 px, 1 line | 46 px | 46 px | `ui-serif` |

### Other checks

| Check | Result |
|---|---|
| `body` computed family | `system-ui` (sans) at every width/page |
| Form label (`.field__label`, login) | `system-ui` — serif **not** applied to controls |
| Component heading (`.hero__panel h2`) | `ui-serif`, 19 px (1.2 rem — display-level rule applies to `h2`; size unchanged) |
| Single `h1` per page | ✅ `h1Count = 1` at every width/page |
| Horizontal overflow | ✅ **False** at all 24 combinations |
| Navigation wrapping | Collapsed (menu) ≤ 768 px; **1 row, no wrap** at 1024/1440 (2 links logged-out); min link height 39 px |
| Reduced motion (`prefers-reduced-motion: reduce`) | Home: 5/5 `.reveal` fully visible, hero + `::before` animation `none`. `/specialities/`: 0 reveals, nothing animating |
| JavaScript disabled | `h1` still `ui-serif`; 5/5 reveals visible; `html` has no `.js` class — page complete without JS |
| Serif face actually resolves (distinctness probe, same string at 48 px) | serif **848.89 px** vs sans **860.39 px** → **faces differ**, serif did not silently fall back to sans |

---

## 7. Test results

| Check | Result |
|---|---|
| `python manage.py check` | `System check identified no issues (0 silenced).` exit 0 |
| `python manage.py makemigrations --check --dry-run` | `No changes detected` exit 0 |
| `python manage.py test` | **Ran 205 tests … OK (skipped=1)** exit 0 |
| `pytest -q` | **204 passed, 1 skipped** exit 0 |
| `git diff --check` | exit 0 (CRLF notices only) |
| CSS brace balance | **378 open / 378 close** (unchanged from baseline) |
| `styles.css` line count | 1758 (was 1732; +26 lines, all tokens/comments) |

Test counts match the pre-change baseline exactly (205 OK / 204 passed, 1 skipped) — no regression.

---

## 8. Issues, observations and fallback decisions

1. **Serif weight resolution.** Headings declare `font-weight: 600`. System serifs (Georgia,
   Palatino) ship only Regular/Bold cuts, so per the CSS font-matching algorithm a declared 600
   resolves to the **Bold (700)** cut. Computed `font-weight` still reports the declared `600`.
   This is consistent across all headings (no uneven weight) and is the expected, intentional
   editorial treatment. No action needed.
2. **Small `h2`s now serif.** The hero panel heading ("Find a doctor", 19 px) and empty-state
   headings inherit the section-heading serif via the global `h2` role. This is the intended
   consequence of the display-level rule (a heading is a heading on every route); no size,
   spacing, layout or control of those components was changed.
3. **Auth and dashboard `h1`s inherit the page-heading serif.** Deliberate: one page-heading voice
   across the site. No auth/dashboard layout, form, table or control was altered — typography only.
4. **Numerals deliberately kept sans** (`.stat-value`, `.trust-value`, `.step::before`,
   `.ticket__date`, `.about-steps` counters). System serif figures are old-style; keeping
   numerals sans protects tabular alignment and the existing `font-variant-numeric: tabular-nums`
   behaviour.
5. **No single-sans fallback needed (D1 from the plan).** The serif stack resolved to a genuinely
   distinct face (measured width differs from sans), so the Phase-1b fallback was **not** taken.
6. **Cross-platform limitation.** Only Windows + system Chrome could be measured in this
   environment. macOS/iOS/Android/Linux rendering of the `ui-serif` → Palatino/Georgia/Noto
   fallback chain is reasoned from the CSS stack, **not** measured. If a later review finds the
   serif too variable, the documented fallback is a single sans with a committed display weight.
7. **Pre-existing items, out of scope, unchanged:** the `.eyebrow` ALL-CAPS label (Phase 2),
   nav link tap-target 39 px, `.date-chip__dow` at 0.72 rem, the appended-arrow CTA (Phase 4/6).
   These are not regressions from this phase.
8. **No perceptual review possible.** This environment has **no image input**, so all verification
   above is quantitative (computed styles + geometry). No claim of visual/perceptual review is made.

---

## 9. Confirmation — pre-existing uncommitted work preserved

- The working tree contained a large pre-existing changeset before this phase (README, forms,
  ~36 templates, `styles.css`, views, docs, `static/js/`, `templates/partials/`).
- `git status --short` after this phase shows the **same set of modified/untracked files** as
  before, plus the new `docs/phase-7.5-typography-report.md`. No pre-existing file was reverted,
  discarded, stashed or cleaned.
- **Prohibited operations were not used:** no `git reset`, no `git checkout`/`git restore` to
  discard, no `git clean`, no destructive `git stash`.
- `styles.css` was edited in place via targeted string replacements only; the full-file `git
  diff` appears large solely because `HEAD` is the pre-Phase-7 baseline (the file was already
  substantially rewritten in the uncommitted Phase 7.x work).

---

## 10. Scope confirmation

Only Phase 1 typography tokens and their consumers were implemented. **No** Phase 2 work (eyebrow
removal, heading-measure unification), card, hero, form, auth, dashboard, motion or component
redesign was performed. Nothing was committed or pushed.
