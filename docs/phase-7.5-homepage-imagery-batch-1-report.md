# Homepage imagery — Batch 1 report (hero + About + speciality tiles)

> Executed 2026-10-18 per user instruction: the first visible imagery batch
> (plan §6B.5 IMG-P2 scope) was pulled **ahead of H3-H6**. Photo-first
> implementation in this batch is limited to approved **atmosphere imagery**
> per plan §6B.1. **Nothing staged, committed or pushed**; no model, route,
> setting or dependency change; the working booking form, navigation, hero
> ids/anchors and all §K contracts are untouched.

## 0. Sourcing & licences (STEP 2)

- Licence verified **directly from pexels.com/license/** (2026-10-18): free
  commercial use incl. websites; attribution optional; modification allowed;
  no implied endorsements; no redistribution as stock.
- 7 photographs chosen from Pexels contributor pages, **downloaded to
  static/img/**, each **individually opened and visually inspected**
  (subjects match intended use; no branding, no off-direction imagery).
- Per-asset records (source, licence, source date, photographer, dimensions,
  alt, intended use): **docs/imagery-licensing.md** (new).
- Photographers credited: RDNE Stock project · Ivan Babydov · Thirdman ·
  Gustavo Fring ×2 · Funkcinės Terapijos Centras · Pavel Danilyuk.
- Honesty controls applied: hero Alt describes the scene generically; About
  caption opens with **"Illustrative stock photo —"**; card tiles are
  decorative (`alt=""` + `aria-hidden` wrapper) because the card title
  carries the meaning; **doctor cards keep initials avatars** — no stock
  portrait stands in for a real doctor.

## 1. Files changed

| File | Change |
|---|---|
| `static/img/home/hero-main.jpg` | **New** — hero photograph (1600×1200, 144 KB). |
| `static/img/about/waiting-area.jpg` | **New** — About figure (1200×960, 83 KB). |
| `static/img/specialities/<slug>-card.jpg` ×5 | **New** — one tile per real speciality slug (cardiology, dermatology, general-medicine, orthopaedics, paediatrics; 900×600, 36-59 KB each). |
| `website/templatetags/clinic_images.py` (+`__init__.py`) | **New** — `static_exists` filter: renders a tile only when its file exists in `STATICFILES_DIRS`/`STATIC_ROOT` → graceful text-only fallback, never a broken `<img>`. No dependency (std-lib filesystem probe). |
| `templates/partials/_speciality_card.html` | Optional `.service-card__media` photo block (slug-keyed + existence-checked, `aria-hidden`, `alt=""`, `width/height` set, lazy). Shared partial → speciality list page gains the same tiles. |
| `templates/home.html` | **(i)** Hero right column is now `.hero__aside`: photograph + the **unchanged** booking form panel, overlapping the photo's lower edge (`.hero__panel` markup untouched — same `h2`, doc, form, `hero-speciality` id, `GET → doctor_list`). **(ii)** About band: copy left + `_figure_plate.html` **photo branch** right (`image_url/width/height` + honest caption). Hero img: `width/height` attrs, `fetchpriority="high"`, `decoding=async`. |
| `static/css/styles.css` | `.hero__aside`/`.hero__photo` (4/3 reserved geometry, radius, brand hairline) + `.hero__panel` overlap (`margin-top: -var(--sp-7)`, border `--line-strong`). Removed the floating decorative `.hero::after` card (base + ≤768 rules) — it would have collided with the photograph; the photo is now the hero's one visual anchor. `.figure-plate__frame img` (absolute inset 0, `object-fit: cover`) added beside the svg rule. `.about-grid` → 2-col grid (copy 1.05fr / figure 0.95fr, align center); `.service-card__media` (3/2 reserved, radius, hairline). ≤900: hero aside max-width 26.5rem, `.about-grid` stacks (figure after copy). Tokens only. |
| `docs/imagery-licensing.md` | **New** manifest (above). |

Unchanged by design: `_doctor_card.html` (initials avatars), `_figure_plate.html`
SVG branch (H2 planner band remains the SVG) — see §3; `static/js/app.js`,
all views/urls/tests/models/settings.

## 2. Verification performed

- `manage.py check`: clean; `makemigrations --check --dry-run`: no changes;
  `git diff --check`: exit 0 (benign CRLF notices).
- **`manage.py test`: 228 tests, OK, skipped=1. pytest -q: 227 passed, 1 skipped.**
- Offline render (rolled-back test client, `DB_ENGINE=sqlite`): home 200,
  speciality_list 200, doctor_list 200.
- Headless-Chrome QA (fresh script, `phase-img/qa.mjs`), **with images
  force-loaded and reveals scroll-triggered before probing**:

| Check (page/width) | 390 | 768 | 1024 | 1440 |
|---|---|---|---|---|
| Overflow / h1 / console errors — home | 0/1/0 | 0/1/0 | 0/1/0 | 0/1/0 |
| `<img>` total on home (hero + about + 5 tiles) | 7 | 7 | 7 | 7 |
| Broken imgs / non-local (hotlink) srcs | **0/0** | 0/0 | 0/0 | 0/0 |
| `.service-card__media` count / natural size (home + list) | 5, each 900×600 natural in a 3/2 reserved box | 5 | 5 | 5 |
| `.about-grid` columns (home) | 1 | 1 | 2 | 2 |
| About plate aspect | 1.25 (5/4) | 1.25 | 1.25 | 1.25 |
| Hero photo natural/box aspect | 1600×1200, 1.33 | same | same | same |
| Panel overlap (negative margin) | yes | yes | yes | yes |
| Template-comment leak / `{%` | false | false | false | false |
| Overflow / h1 / errors — speciality_list | 0/1/0 | 0/1/0 | 0/1/0 | 0/1/0 |

Full-page screenshots (8) captured in `Temp\opencode\phase-img\shots\` and
**genuinely inspected** (image reading verified in prior session):

- **1440 home:** hero reads as designed — serif headline left; photograph +
  overlapped booking panel right (form intact, "Find a doctor" panel floats on
  the photo's lower edge); planner-SVG band intact; About copy + consultation
  room photo + honest caption; **5 speciality cards each with its topical
  tile**; doctors band retains initials avatars; flat CTA band; footer normal.
- **390 home:** stacked hero (copy → CTAs → photo → panel-overlap) reads
  cleanly with no overlap of faces; sections/action targets unchanged.
- **1440 speciality_list:** the shared card partial renders the 5 tiles in a
  tidy 3-column editorial grid (project-wide consistency already achieved via
  the partial, no extra page work).
- Notes (minor, non-defect): hero photo's subject faces remain visible above
  the panel overlap at all widths; the About photo's caption is longer than
  the note-style captions — intentional (honesty statement).

## 3. Scope decisions recorded (STEP 3.4 compliance)

- **H2 planner SVG retained** in `.band--viz` (no strong reason to change; the
  About photo + hero photo are already two substantial image moments — a third
  photo there would homogenise the bands).
- **Doctor portraits not introduced.** Real doctors (Aswin Kumar, Meera Nair,
  Rahul Verma) keep initials avatars per the no-stock-portrait rule; the
  `Doctor` model has no image field (ADR-015 unchanged, no migration).
- Coverage ordering per user instruction: batch 1 (this report) → human
  review; then batches for doctor pages, speciality detail, auth panel,
  transactional restrained headers, dashboards — **restraint preserved where
  the workflow requires it** (forms/tables stay image-free inside their
  working area).

## 4. Revision 2 (2026-10-19): full-bleed photographic hero

The user approved batch 1's direction (photos, typography, colours, booking
form) but wanted the hero photograph to be a **full-bleed background** behind
the whole hero — Hospic-style: photo as background, restrained dark
teal/navy overlay, transparent navigation above, large foreground text.
Scoped strictly to the hero: no new assets (same licensed
`static/img/home/hero-main.jpg`, already in `docs/imagery-licensing.md`),
no other pages, no logic/URL/model changes, About photo / 5 speciality
tiles / H2 planner-SVG band untouched.

### Files changed in revision 2

| File | Change |
|---|---|
| `templates/home.html` | Hero right-column photo card (`.hero__aside`/`.hero__photo`) **removed**; the booking panel (`.hero__panel`, markup/ids/form unchanged) sits directly in the grid as the right column. A full-bleed `<img class="hero__bg">` (same hero asset, `alt=""` + `aria-hidden="true"` — decorative, per §5) is the hero's first child: `width/height` set, `fetchpriority="high"`, `decoding=async`. |
| `static/css/styles.css` | `.hero__bg` = absolute `inset:0`, `object-fit:cover`, `object-position:50% 32%` (keeps both subjects in frame at every width, no distortion, zero layout shift). `.hero::before` pictogram wash **replaced by the overlay**: vertical top band for nav legibility + horizontal teal gradient (dark left → lighter right) — `rgba(4,48,50,0.9)/0.74/0.42/0.6` stops. `.hero > :not(.hero__bg)` stacks copy/panel/… above the bg layer. `.hero__panel` overlap/negative margin removed (plain white card again). `@keyframes hero-bg` end-state fixed `0.4 → 1` (see debug below). ≤900: `.hero` gets real vertical presence (`min-height:min(82vh,700px)`) and a vertical-gradient overlay (dark behind the text upper half → lighter lower band so the photo remains clearly visible; not a solid-teal block). Reduced-motion handling unchanged (still removes the animation; overlay paints at full strength). |

### Bugs caught and fixed during revision

1. **Overlay at 40% opacity on desktop** — the legacy hero entrance
   animation (`@keyframes hero-bg … to { opacity: 0.4 }`, written for the
   old pictogram wash) was still fading `::before` to 0.4, so with the photo
   behind it the hero read as almost no overlay. Probe of
   `getComputedStyle(.hero,'::before')` showed `opacity: 0.132675` mid-run;
   keyframe end state corrected to `opacity: 1`. Reduced-motion still
   short-circuits it (existing block).
2. **Collapsed mobile hero / near-solid teal** — first mobile pass used a
   uniform flat overlay with `min-height:auto`; screenshot inspection showed
   the photograph barely perceptible (the exact failure mode the brief
   forbids). Replaced with 82vh/700px presence + vertical gradient
   (0.85 → 0.3): text zone protected, photo clearly visible below.

### Verification (revision 2)

- `manage.py check` clean; `makemigrations --check --dry-run`: no changes;
  `git diff --check`: OK (benign CRLF notices); `pytest`: **227 passed,
  1 skipped**.
- Headless-Chrome QA re-run at 390/768/1024/1440 (home + speciality list):
  overflow 0 · broken imgs 0 · non-local srcs 0 · console errors 0 ·
  one `h1` per page · 7 imgs (home), 5 (list) at every width.
- **Genuine screenshot inspection at all four widths** (hero-region crops
  from the fresh full-page shots): full-bleed photo edge to edge; desktop
  shows transparent nav above the photo with legible white links; serif
  headline/lead/CTAs over the darkened left band; white booking panel
  layered above the photo right; both photo subjects visible without
  distortion at 1024/1440; tablet (768) keeps image + copy + full-width
  panel without overlap; mobile (390) is compact but substantial — copy and
  actions readable top, photograph clearly visible lower band, opaque white
  form usable. Trust strip (5 specialities / 3 doctors) directly below.

### Revision-2 limitations

1. The lead paragraph's final words sit over the photo's brightest midband
   at 1024/1440; legibility verified visually but the weakest contrast spot
   of the hero — if it still feels light, next nudge is raising the 48%
   gradient stop (0.74 → ~0.78).
2. Reduced-motion and no-JS behaviour unchanged from batch 1 (overlay
   paints statically at full opacity in both cases) — not re-run through
   the flags harness this pass; DOM checks only.
3. Same asset constraints as §4 above (JPEG, no srcset variants; new list
   in manifest unchanged — no new photo downloaded).

## 5. Contract / constraints audit

- One `h1`; `#doctors`, `#about-heading`, `#viz-heading`, `#services-heading`,
  `#cta-heading` all intact; hero form + register CTA unchanged; §K.5 strings
  preserved (full test suite green).
- No model/migration/route/dependency/settings change; ADR-020 respected
  (self-hosted, no CDN/framework/webfonts).
- Git: files changed across both passes: §1 table (batch 1) + revision-2
  table above; **nothing staged/committed/pushed**; all pre-existing
  modifications and untracked files preserved (status count unchanged by
  revision 2); no destructive git commands.

**Status: STOP — hero full-bleed revision 2 complete and awaiting human
review before rolling the imagery system through the rest of the project
(STEP 4 batches).**
