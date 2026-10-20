# Phase 7.5 — Phase 2: Editorial Labels and Heading Measures
**Date:** 2026-10-18  
**Status:** Complete (implementation + verification). **Do not commit or push.**

> Phase 1 was preserved. The `frontend-design` and `web-design-guidelines` skills were loaded. No changes to Django models, views, forms, URLs, settings, migrations, authentication, RBAC, booking logic, or database configuration.

## 1. Files Changed

- **`static/css/styles.css`** — editorial labels + measure refinements (1 file).  
  - Added `--measure-body: 58ch` alongside `--measure-heading: 64ch`; comment clarified heading wrappers.  
  - Replaced `.eyebrow` styling: from tracked-out ALL-CAPS to restrained editorial label (sentence case, `font-family: var(--type-support-font)`, `font-weight: 600`, `letter-spacing: 0.02em`, `display:block`, `margin:0 0 var(--sp-2)`, `color: var(--brand-700)`). Semantic content unchanged.  
  - `.page-head p`: added `max-width: var(--measure-body)`.  
  - `.section-header p`: added `max-width: var(--measure-body)`.

No template files were edited. No new files created. No JavaScript, fonts, assets, or dependencies added.

## 2. Editorial Labels (Eyebrows)

**Before:** uppercase, tracked (`0.1em`), inline-block, heavier spacing.  
**After:** sentence case, quiet tracking (`0.02em`), block, support font, tighter margin.

**Live verification (home.html, @1440):** 3 labels ("About the clinic", "Specialities", "Our doctors") — text unchanged; `text-transform: none`, `display:block`, `weight:600`, `letterSpacing:0.256px`, `size:13px`, support font; sit above headings, quieter than headings, visible, not clipped. Other pages have 0 eyebrows.

## 3. Heading Measures

- Added `--measure-body: 58ch` consumed by intro paragraphs.  
- `.page-head p` → 58ch; `.section-header p` → 58ch.  
- `.band__head` remains 64ch (wrapper), `.section-intro` remains 58ch.  
- `.dashboard__head` unchanged (no max-width; intentional).  
Computed @1440: `.page-head` 552px (64ch), `.page-head p` ~500.25px (58ch); `.band__head` 552px; `.section-intro` ~562.78px.

## 4. Responsive Verification (390/768/1024/1440)

6 pages × 4 widths (24 combinations): **no overflow**; **h1Count=1** everywhere; eyebrows only on homepage — visible, inside parent, not clipped at any width; nav rows 1 @1440, collapses ≤768, min link height ≥39px.

## 5. Wrapping / Widows

Hero H1 and band section-title render as 2 lines @1440 with no widows; list/detail page h1s typically 1 line. `text-wrap: balance` preserved on `h1–h4`.

## 6. Reduced Motion & No-JS

Reduced motion: 5 reveals all visible on home, hero animation `none` (and `::before` none); `/specialities/` 0 reveals. No-JS: `html.js` absent, h1 uses serif, 3 eyebrows visible with no uppercase, reveals visible — behavior unchanged vs Phase 1.

## 7. Tests / Checks

- `manage.py check` → 0 issues  
- `makemigrations --check --dry-run` → no changes  
- `manage.py test` → **205 OK (skipped=1)**  
- `pytest -q` → **204 passed, 1 skipped**  
- `git diff --check` → exit 0 (CRLF warnings only)  
- CSS braces **378/378**, lines 1762  
- Templates compile; eyebrow labels in `home.html` unchanged.

## 8. Preserved Work / Scope

All pre-existing uncommitted work preserved; only `static/css/styles.css` changed among app files. Selective serif for h1/h2 preserved; numerals/UI remain sans. No card/hero/form/dashboard/nav/layout/motion redesign. Exceptions: `.dashboard__head` no max-width; eyebrows only on homepage with restrained treatment; wrapper measure (64ch) separated from intro paragraphs (58ch).

## 9. Limitations

No perceptual screenshot review (quantitative only). Cross-platform serif rendering not re-measured (unchanged). Serif 600 resolves to Bold cut (intentional).

**Conclusion:** Phase 2 objectives met. No regressions. Stop for review before Phase 3.