# Phase H2 report — Dedicated visual section (homepage)

> Scope executed: **H2 only** (the dedicated visual band + photo-ready figure plate,
> per `docs/homepage-reference-analysis-and-execution-plan.md` Rev 2 §6A/§10).
> **Nothing staged, committed, pushed.** H3–H7 were **not** started.
>
> **Revision 2 (H2 review response).** After human review of the mobile screenshots, the
> report now adds §6 (a rendering-bug investigation) and §7 (the follow-up fix, design
> correction and re-verification). §§1–5 are the original H2 record, retained as history.

## 6. H2 review response — rendering bug (investigation BEFORE any change)

**Symptom reported:** raw text beginning `{# Original editorial illustration: a week of
availability...` visibly rendered behind/overlapping the planner illustration in the new
band (worst on mobile).

**Evidence gathered (no code changed during investigation):**
- `templates/partials/_figure_plate.html` (the only file containing the string
  "Original editorial illustration"): the inline note at lines 25–27 opened with `{#` but
  **closed with `%}` instead of `#}`** — mixed delimiters. Every other template in the repo
  uses proper `{% comment %}…{% endcomment %}` blocks (verified by searching for `{#`,
  `{% comment`, and `#}` repo-wide: exactly one malformed comment, this one).
- Rendered offline HTML (both `home_anon` and `home_patient`): the malformed comment text
  was present verbatim inside `.figure-plate__frame`, before the `<svg>`.
- Mechanism, confirmed against the installed interpreter
  (`C:\venvs\anmaya-clinic\Lib\site-packages\django\template\base.py:90`):

  ```python
  tag_re = re.compile(r"({%.*?%}|{{.*?}}|{#.*?#})")
  ```

  A Django comment token must end with `#}`. Because the blob ends with `%}` and no `#}`
  exists anywhere later in the file, **no comment token ever matches**. The lexer falls
  through and emits the region as a plain **TEXT token** — and since the next template
  construct is `{% endif %}`, that single text token carries the comment text *and the
  entire `<svg>…</svg>` markup verbatim* into the HTML. The browser still parses the
  literal `<svg>` as an element, so both "rendered": the text printed at the frame's
  top-left while `.figure-plate__frame svg { position: absolute; inset: 0 }` layered the
  artwork over it — the visible overlap.
- **Why the earlier QA missed it:** the probe checked SVG geometry/attributes and section
  layout but never the frame's raw text content; template text leaks produce no console
  errors and no layout shift. A dedicated leak-probe is now part of the QA script (§7).

## 7. Fix, design correction and re-verification (after root cause confirmed)

### 7.1 Bug fix — removed at source (no CSS workaround)

- The malformed inline comment was **deleted** from `_figure_plate.html`; its content was
  folded into the file's valid top `{% comment %}…{% endcomment %}` documentation block.
- No other template change. The `<img>` photo-ready branch, `viewBox`, `aria-hidden`,
  `focusable="false"` and the real `figcaption` are preserved.
- **Regression probes added** to the QA script: `frameRawTextLength` (must be 0),
  `bodyContainsTemplateComment`/{%`-scan, `figureElementCount` (must be 1), and
  `visibleTemplateText`. Rendered-HTML grep also asserts `0` occurrences of `{#` and of
  "Original editorial illustration", and exactly **one** `<figure>` on the page with none
  inside the About band.

### 7.2 Design correction — deliberate visual focal point (still H2 scope)

Reviewer feedback: the SVG was "too small and abstract". Rebuilt the illustration and the
plate ground (same two files, no scope expansion):

- **Ground:** `.figure-plate--lg .figure-plate__frame` changed from light
  (`--brand-050`/`--brand-200` hairline) to **deep brand teal `--brand-700`** with a
  `--brand-800` hairline. The plate now reads as an image/poster — the strong image-led
  moment of the band — while remaining flat and two-dimensional (no gradients, no layer).
- **Composition (720×480, slice-safe margins):** one large white planner card
  (rounded 28px, x56–x664, y48–y416) carrying: a **7-day week grid** (8 hairline verticals,
  3 horizontals), **day ticks**, **six slot pills** (one solid confirmed slot with a white
  check; one soft "held" slot; four open slots with centre dots, receding opacity), a
  **dotted "now" time-marker** with a top dot, and a **dotted route with arrow chevron**
  flowing from the confirmed slot to the next opening. All artwork stays inside the card
  inside the plate — the defined visual container; nothing bleeds or overlaps.
- Still palette tokens only, no clinical imagery, no claims — decorative `aria-hidden`
  art; meaning stays in the caption text. The approved-image path is unchanged: supply
  `image_url` to the same partial for an approved, self-hosted clinic photograph (H7).

### 7.3 Re-verification results (fresh offline render + fresh screenshots)

`manage.py check` clean; `makemigrations --check --dry-run` "No changes detected";
**`manage.py test` 228 OK (skipped=1)**; **`pytest -q` 227 passed, 1 skipped**;
`git diff --check` exit 0 (benign CRLF notices only). Home renders 200 anon + patient.

| Check | 390 | 768 | 1024 | 1440 |
|---|---|---|---|---|
| Overflow / `h1` / console errors (both pages) | 0/1/0 | 0/1/0 | 0/1/0 | 0/1/0 |
| Frame raw-text length (leak probe) | **0** | **0** | **0** | **0** |
| Template-comment text visible in body | **false** | **false** | **false** | **false** |
| `<figure>` count (page / in About) | 1 / 0 | 1 / 0 | 1 / 0 | 1 / 0 |
| Frame aspect | 1.33 | 1.78 | 1.50 | 1.50 |
| `.viz-grid` columns | 1 | 1 | 2 | 2 |

Plus: frame background `rgb(11,124,128)` = `--brand-700`; caption contrast 4.61,
rail `h2` 13.99, intro 4.61 (all ≥ AA); genuine **no-JS** pass
(`--blink-settings=scriptEnabled=false`, `html.no-js`, band at opacity 1 with identical
reserved geometry) and genuine **reduced-motion** pass (`--force-prefers-reduced-motion`,
transitions neutralised ~1e-06s). Rendered-HTML greps: `{#` ×0, "Original editorial
illustration" ×0, `<figure` ×1.

### 7.4 Actual visual inspection performed (screenshots genuinely viewed)

This session's tooling returned the PNGs as viewable images, so the following were
**actually looked at, not just measured**:

- **Mobile 390 (`home_anon_band_390.png`):** the teal plate + white planner card render
  cleanly; **no raw text overlapping the artwork**; confirmed slot/check, route with
  chevron, "now" marker and day ticks all legible at the small size; caption sits below
  the plate; rule/eyebrow/serif `h2`/intro rail reads correctly.
- **Desktop 1440 (`home_anon_band_1440.png`):** the 2-column band reads as a deliberate
  feature — large teal plate left, serif rail right; the illustration is a clear focal
  point, not an enlarged icon; caption aligned under the plate.
- Minor notes (not defects): the card's bottom margin is marginally larger than its top
  margin by design (y48 top / y64 bottom); the dotted "now" line stops short of the
  card bottom deliberately so it reads as a time cursor rather than a rule.
- 16 fresh screenshots (full-page + band-scrolled, both pages, 4 widths) saved in
  Temp `phase-h2/shots/` for the reviewer.

### 7.5 Remaining limitations after the correction

1. Imagery remains **original SVG** until an approved, licensed clinic photograph is
   supplied (H7 deferred; the same partial slot accepts it without markup changes).
2. Perceptual review is necessarily limited to the screenshots actually viewed in this
   session (mobile 390 and desktop 1440 band crops, plus full-page greps); the reviewer
   may still judge composition/quality differently.
3. `doctor-card__qual` contrast 4.42 remains untouched — H3 scope, as before.
4. Nothing staged/committed; all pre-existing modified and untracked files preserved;
   no destructive git commands; no model or migration changes.

## 0. Approved decisions applied

| Decision | Value |
|---|---|
| Placement | **(a)** new `section.band.band--viz` **between the trust strip and the About band** |
| Image strategy | **Original in-repo SVG illustration** in a photo-ready slot |
| H7 (licensed photo) | **Not started** — no approved clinic photograph confirmed |

## 1. Files changed (only)

| File | Change |
|---|---|
| `templates/partials/_figure_plate.html` | **New.** Reusable, photo-ready figure plate. Photo-first when `image_url`(+) is supplied (`<img>` with `alt`, optional `width`/`height`, `loading="lazy"` default), otherwise the original inline SVG illustration. Always renders a real `figcaption`. |
| `templates/home.html` | **(i)** New `.band--viz` section between the trust strip and About: figure plate + `.viz-rail` (rule/eyebrow/`h2#viz-heading`/intro). **(ii)** About band: inline `figure.figure-plate` **removed** (consolidated into the visual band per plan §7.3); copy, `h2#about-heading`, `ol.about-steps` unchanged. 182 → 180 lines. |
| `static/css/styles.css` | `.about-grid` → copy-only block with `--measure-heading` (1444–1445) since its second column is gone. New `.figure-plate--lg` frame (light `--brand-050` ground + `--brand-200` hairline, `aspect-ratio 3/2`, 1468–1473) and caption spacing. New `.viz-grid` (2-col `1.5fr/1fr`) + `.viz-rail` (1506–1512). Responsive: ≤900 stacks to 1 col + `16/9` frame (1751–1752); ≤640 `4/3` frame (1828). Obsolete ≤760 rules (about 1-col, `.figure-plate{order:-1}`, `16/10`) removed. **Tokens only** — no new colours/fonts/motion. |

`static/js/app.js`, `website/tests.py`, all shared card/empty partials, URLs, views,
settings and models: **untouched**. Full `manage.py test` + `pytest` both **green**
(228 OK skipped=1; 227 passed 1 skipped) — no regression anywhere in the suite.

## 2. The illustration (original, in-repo)

Problem answered directly: the old About plate was a single generic
medical-cross/heartbeat glyph. The new artwork is a **compositional, product-true
"availability" scene**, 720×480, authored for this repo:

- a planner card (hairline `--brand-700` border on `--brand-050` ground) with a header rule;
- a **5×4 week grid** with **day-header ticks** and **time ticks**;
- **three slot cards**: one **confirmed** (solid `--brand-700` + white check), two **open**
  (outlined, receding opacity);
- a **dotted wayfinding route** (`--brand-600`) flowing from the booked slot to the next
  opening, ending in a chevron — the booking journey, not a medical icon;
- a quiet analog-time cue bottom-left for balance.

Flat and two-dimensional (depth stays in the hero only), palette tokens only, hairline
strokes, generous negative space — per the art-direction brief (plan §7.2.1). Decorative:
`aria-hidden="true" focusable="false"`; all meaning is carried by the real caption text.
No clinical imagery, portraits, claims, statistics or testimonials.

## 3. Verification performed (all quantitative)

Offline rolled-back test-client render → offline HTML → headless Chrome (`home_anon`,
`home_patient`; HTML reports + screenshots in Temp `phase-h2/`).

| Check | 390 | 768 | 1024 | 1440 |
|---|---|---|---|---|
| Horizontal overflow | 0 | 0 | 0 | 0 |
| `h1` count / console errors | 1 / 0 | 1 / 0 | 1 / 0 | 1 / 0 |
| `.band--viz` sections | 1 | 1 | 1 | 1 |
| `.viz-grid` columns | 1 | 1 | 2 | 2 |
| Frame aspect (measured) | **1.33** | **1.78** | **1.50** | **1.50** |
| Frame reserved height | 269px | 397px | 356px | 435px |

- Measured aspect ratios match plan §7.5 exactly (390→`4/3`, 768→`16/9`, ≥1024→`3/2`).
- Band order confirmed: hero → trust → **viz** → about → services → doctors → cta.
- Band background transparent (canvas) — **tint rhythm intact**; no second gradient.
- SVG fills the frame; `aria-hidden`, `focusable="false"`, `viewBox` + `xMidYMid slice`.
- Contrast: caption **4.61**, rail intro **4.61**, rail `h2` **13.99** — all ≥ WCAG AA.
- **Asset integrity:** 0 `<img>` tags; 0 hotlinked hosts (the only external string is the
  SVG XML **namespace identifier**, which is fetched by nothing). No new asset files.
- **Genuine no-JS pass** (Chromium `--blink-settings=scriptEnabled=false`): `html.no-js`,
  band visible at opacity 1 with identical reserved frame geometry at all 4 widths.
- **Genuine reduced-motion pass** (Chromium `--force-prefers-reduced-motion`):
  `matchMedia` reports reduce; reveal transitions neutralised (~1e-06s); final state shown.
- Screenshots captured (13) in Temp `phase-h2/shots/`.

## 4. Explicit limitations (stated honestly)

1. **I cannot view images.** Screenshots at 390/768/1024/1440 were captured for human
   review, but my verification is DOM/CSS/geometry only. I make **no perceptual claim**
   (this is restated from the plan §7.6 caveat).
2. `doctor-card__qual` contrast remains **4.42** (H1 finding) — **intentionally untouched**;
   it is H3 scope.
3. Django's `Emulation` CDP domains were unavailable in the local harness; the no-JS and
   reduced-motion passes were therefore run via genuine browser flags instead of emulation.
4. `.reveal` below-fold opacity 0 is the pre-existing JS-on initial state before the
   IntersectionObserver fires on scroll; the no-JS pass proves content is never hidden.

## 5. Contract / constraints audit

- One `h1`; headings in order; `#doctors` anchor, `doctor_list`/CTA targets, hero form
  `GET → doctor_list`, register CTA (anonymous only) — untouched and rendering.
- No new model/route/dependency/migration (`makemigrations --check`: "No changes detected";
  `manage.py check`: clean). No MEDIA config added. No CDN/web font/framework.
- Editorial direction preserved: section-header grammar reused, tint rhythm intact,
  flat surfaces, tokens only.
- Git: the 45 pre-existing modified files and the untracked set are exactly as before;
  **nothing staged**, no destructive git command.
