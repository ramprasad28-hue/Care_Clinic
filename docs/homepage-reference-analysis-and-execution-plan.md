# Care_Clinic Homepage — Reference Analysis & Execution Plan

> **Status: INSPECTION-ONLY.** This document analyses reference material and the current
> homepage, then proposes an implementation-ready plan. **No application code was changed
> to produce it** (see §13 and the End report). Nothing here is a commitment to build —
> implementation is a separate, explicitly-requested step.
>
> **Revision 2 (H1 review response).** Following review of the H1 baseline report
> (`docs/homepage-h1-baseline-report.md`) and the homepage screenshots, this plan now
> explicitly addresses the **missing image-led visual treatment** (§7), reassesses the
> closing-CTA scope (§5, §10), and corrects the H1-era assumption that `.cta-band` carried
> a gradient (it is already flat — §4.3, §5).
>
> Evidence tags follow `docs/hospic-reference-analysis.md`: **[verified]** (checked
> directly), **[inference]** (reasoned from evidence), **[not verified]** (needs a running
> browser / source we do not have).
>
> **Revision 3 (2026-10-18, project-wide photography strategy).** Per user review, the
> one-photo H7 is **superseded** by a phased, reviewable **project-wide imagery strategy**
> (new §6B): route-by-route image inventory, asset directory + licensing-manifest
> structure, phased implementation (IMG-P0...IMG-P5) with dependencies vs H3-H6, and the
> list of photographs/approvals required. **This revision changes planning only** - no
> template, CSS, JS, asset, model, settings or dependency change was made. H2 is
> implemented and verified separately (`docs/phase-7.5-homepage-h2-report.md`); H3 is
> started (one CSS contrast edit, tests not yet run) and **paused pending review of this
> revision**. Also corrects the earlier "assistant cannot read images" claims (image
> reading works; the H2 band screenshots were genuinely reviewed - see the §3 note).

---

## 1. Executive summary

- **Goal:** refine the existing Care_Clinic homepage (`templates/home.html`) so it reads as
  a settled, editorial clinical page with a **substantial, image-led visual moment**, using
  the provided references as *grammar only*.
- **Reference situation (important):** a **Larch Health HTML/CSS prototype was requested
  but does not exist on this machine.** A thorough search (project tree, Desktop,
  Documents, Downloads, Temp) found no file or folder named `larch` (the only match was a
  coincidental entry in `.agents/skills/.../library/photos.json`). **Consequently, §2 and
  §3 analyse the Hospic extract + Hospic screenshots instead**, which the user selected as
  the substitute. This must be treated as a deviation from the brief, not a silent
  substitution.
- **H1 review feedback (drives this revision):** the homepage **"lacks a dedicated,
  substantial visual section."** The hero relies on a decorative CSS pattern, the About
  band uses a generic medical-cross/heartbeat SVG, and the speciality/doctor sections are
  text-based. The primary visual identity must not rest on flat colour blocks or generic
  placeholder glyphs. **[observed — H1 baseline + user review]**
- **Asset reality [observed]:** the repository contains **zero image files** (no
  `.png/.jpg/.webp/.svg` outside `.git`/skills); the only URL assets are **two inline SVG
  data-URIs** in the hero CSS (`static/css/styles.css:598,608`). There is **no `MEDIA`
  setting** and no licensed clinic photography. `static/` holds only `styles.css` +
  `app.js`.
- **Current homepage state:** structurally aligned (one section-header grammar, tabular
  real counts, honest ordered list, rule-separated bands). The hero is the **only** gradient
  surface; the closing CTA is **already flat** (solid `#086063`) — contrary to the original
  plan's assumption (corrected in §4.3/§5).
- **What this plan changes (when approved):** add **one dedicated, image-led visual
  section** using an **original, self-hosted SVG editorial illustration inside a
  photo-ready figure plate** (no licensed photo is available yet; a licensed clinic
  photograph can drop into the same slot later). Plus bounded consistency/polish and a
  contrast fix — while preserving every URL name, context variable, form field, permission,
  booking behaviour and the single-`h1` guarantee.
- **Imagery decision (see §7):** **evaluate hero photo vs custom illustration → recommend a
  custom original illustration now**, hero visualisation restrained, with a photo-ready
  slot for approved clinic imagery later. **No hotlinking, no copying of reference assets,
  no invented clinic photographs or doctor portraits.**
- **Biggest risks:** (a) no licensed photography (mitigated by an original SVG + a
  photo-ready slot); (b) the illustration reading as generic clip-art (mitigated by an
  art-direction brief); (c) content truthfulness; (d) not breaking the booking contract;
  (e) the Larch substitution above.
- **Plan shape:** **7 bounded, independently testable phases** (§10). Each ends green
  (`check`, no migrations, `manage.py test`, `pytest`, `git diff --check`) and is reviewable
  on its own before the next begins. **H2 is re-scoped** from "flatten the CTA" (moot) to
  the **dedicated visual section**.

---

## 2. Analysis of the reference HTML/CSS

### 2.0 Substitution note (Larch Health)

- **Requested:** "Larch Health HTML/CSS prototype".
- **Found:** nothing. **[verified]** Searches of the project workspace, `Desktop`,
  `Documents`, `Downloads` and `Temp` returned no `larch` file/folder. The only hit was
  `.agents/skills/design-taste-frontend/library/photos.json` (unrelated). **[verified]**
- **User decision:** *"Use Hospic extract + screenshots."*
- **Consequence:** every statement below about "the reference" refers to **Hospic**, not
  Larch Health. If a Larch prototype is later supplied, §2/§3/§5 must be re-done.

### 2.1 What the Hospic reference actually is **[verified]**

- A **Framer template export** copied into a Next.js shell whose README states
  *"What this is not: Source you can edit."* The real markup is pre-rendered snapshot HTML
  driven by a client-side Framer runtime (`.mjs` chunks).
- Extract inspected earlier:
  `C:\Users\Ramprasad\Downloads\hospic-hospital-healthcare-framer-template-copy-site (1)\index.html`
  — **923,876 bytes** **[verified]**. Sibling `about/` and `pricing/` also exist.
  (A second export, `...-copy-exact-next`, is analysed in `docs/hospic-reference-analysis.md`.)
- Navigation/section tokens in the snapshot `index.html` (counts, **[verified]**):
  `Our Services` ×1, `Departments` ×1, `Book an appoinment` ×1, `Testimonial` ×1,
  `FAQ` ×1, `Pricing` ×1, `Doctors` ×1, `Footer` ×1, `Glass Effect` ×1, `Smooth Scroll` ×1.
- Headings observed in the snapshot (**[verified]**, sanitised):
  *"Exceptional care Better health"*, *"Excellence in every medical service"*,
  *"Specialized departments for complete healthcare"*, *"Affordable health packages for
  every need"*, *"Trusted healthcare, trusted voices"*, *"Meet our experienced doctors for
  care"*, *"Frequently asked questions"*, *"Latest health insights and wellness tips"*.

### 2.2 Is the reference's HTML/CSS *reusable*? — No, as source **[verified]**

- Licensing: Hospic is a **commercial Framer template**; reuse is not licensed.
- The CSS present is the **Framer bundle**, not authorable source; the "HTML" is a
  generated snapshot. There is no hand-authored stylesheet to adapt.
- Therefore the reference is treated **strictly as a design grammar source** (layout,
  rhythm, header idiom, sequencing) — never copied. **This includes imagery:** Hospic's
  photographs/videos are **not** used (§7.4).

### 2.3 Transferable grammar extracted (and already largely implemented) **[inference]**

From `docs/hospic-reference-analysis.md` §2.2 and this inspection, the following are the
*only* transferable ideas, all consistent with the approved direction
(`docs/frontend-design-exploration.md` — Concept A "Editorial Clinical" + Concept C
"Modern Medical Journal"):

1. **One reusable section-header block** (rule → label → serif heading → lede).
2. **A short rule above the section label** as the structural lead-in.
3. **A captioned "figure plate"** — a bounded, aspect-ratio visual + an honest caption —
   rather than a full-bleed decorative wash. **This is the seed of §7.**
4. **Large tabular numerals for real counts only.**
5. **A genuine ordered sequence** for process content ("how it works").
6. **Bands separated by rules + spacing**, not alternating shadow washes.

### 2.4 Reference tells that are OFF-direction — do not adopt **[inference]**

- Hero **rating badge** (4.9/5), **packages/pricing**, **testimonials**, **blog/news**,
  FAQ, opening hours, address, phone, social links → **no data / unverifiable claims**.
- **Glassmorphism / gradient washes / drop-shadowed card grids** → off the editorial
  direction.
- **Reference photography / video / illustrations / fonts** → unlicensed; **not** copied or
  hotlinked (§7.4).
- **Web fonts** (Inter + fontshare) → forbidden by ADR-020.
- **Framer / Lenis / GSAP / Three.js runtime** → not added.

---

## 3. Comparison with the Hospic screenshots

> **~~Model limitation~~ Corrected (2026-10-18):** this assistant **can read image
> input** — screenshots during the H2 phase (e.g. `phase-h2\shots\home_anon_band_390.png`
> and `_1440.png`) were **genuinely opened and visually reviewed** (overlap, composition
> and focus checks). The statements below about the Hospic reference keep their original
> basis (documented behaviour in `docs/animation-reference-analysis.md` and
> `docs/hospic-reference-analysis.md`), but the "cannot perceptualise" caveat no longer
> applies to our own screenshots. <br>**Original note (now superseded):** this assistant
> ~~cannot~~ could not read image input at the time this section was written; the PNGs
> below were located but not visually inspected at that time.

- Reference screenshots present at:
  `C:\Users\Ramprasad\AppData\Local\Temp\opencode\shots\hospic_home_{0390,0768,1024,1440}.png`
  **[verified — files exist, not opened].**
- **Local homepage screenshots** also exist (e.g.
  `…\shots\local_home_{0390,0768,1024,1440}.png` and the H1 set
  `…\Temp\opencode\phase-h1\shots\home_anon_{390,1440}.png`) — **[verified — exist, not
  opened]**. The H1 review's observation that the page "lacks a substantial visual
  section" is accepted as reported, but this planning pass **cannot independently
  perceptualise** it; the quantitative H1 baseline (0 images, text-led bands) corroborates
  the structural claim.
- Documented reference behaviour (from `docs/animation-reference-analysis.md`): hero visual
  scale `1.1 → 1` + fade; hero text `translateY(120px → 0)`; **one-shot** reveals; stat
  counters; FAQ accordion `250–320 ms`; non-sticky header; Lenis smooth scroll.
- Care_Clinic's decided translation (kept) **[verified in CSS]**: opacity/transform only,
  one-shot `IntersectionObserver` reveals (`styles.css:1696–1705`), neutralised under
  `prefers-reduced-motion` (`styles.css:1818–1835`), usable with JS off. **No Lenis/GSAP.**
- **Net:** Care_Clinic matches Hospic's *intent* without its runtime. The **remaining gap is
  imagery** (Hospic leads with photography; Care_Clinic has none) plus consistency — see §7.

---

## 4. Current homepage architecture

### 4.1 Request/render path **[verified]**

- `config/urls.py` includes `website.urls` **un-namespaced** (preserves `home`) plus
  `admin/`, `accounts/`, `clinic/`, `appointments/`, `dashboards/`.
- `website/urls.py` names: `home`, `speciality_list`, `speciality_detail`, `doctor_list`,
  `doctor_detail`.
- `website/views.py` → `HomeView(TemplateView)`, `template_name = "home.html"`.
  Context: `specialities = Speciality.objects.active()[:6]`,
  `doctors = Doctor.objects.public()[:6]`, `speciality_count`, `doctor_count`.
- Settings is a **package** (`config/settings/{base,development,production}.py`), not a
  single file. `base.py`: `STATIC_URL="/static/"`, `STATICFILES_DIRS=[BASE_DIR/"static"]`,
  `TEMPLATES DIRS=[BASE_DIR/"templates"]`. **No `MEDIA_URL`/`MEDIA_ROOT`** is configured
  **[verified]** — relevant to §7 (self-hosted static imagery needs no MEDIA plumbing).

### 4.2 Template structure (`templates/home.html`, 182 lines) **[verified]**

> **Snapshot note (2026-10-18):** `templates/home.html` is now **180 lines** and no longer
> matches this pre-H2 table: H2 removed the About figure, added the dedicated
> `section.band.band--viz` between the trust strip and About (with the new
> `templates/partials/_figure_plate.html`), and normalised the About band to copy-only.
> See `docs/phase-7.5-homepage-h2-report.md` for the current state. The H2/H3 CSS changes
> also shifted the §4.3 line ranges; treat §4.2/§4.3 as the Phase-7.5 baseline snapshot.

| # | Section | Key classes / ids | Data |
|---|---------|-------------------|------|
| — | blocks | `title`, `main_class="main--flush"`, `header_class=" site-header--hero"` | — |
| 1 | Hero | `.hero` › `.hero__grid` › `.hero__copy` (`.hero-badge`, `h1`, `.hero__lead`, `.hero__actions`) + `.hero__panel` (form `GET` → `doctor_list`, `select[name=speciality]#hero-speciality`) | `specialities` |
| 2 | At-a-glance band (conditional) | `.band.band--compact.reveal` › `.trust-strip` (`.trust-item` › `.trust-value` + `.trust-label`) | `speciality_count`, `doctor_count` |
| 3 | About band | `.band.band--tint.reveal` › `.about-grid` = `.about-copy` (`.section-rule`, `.eyebrow`, `h2#about-heading`, `.section-intro`, `<p>`, `ol.about-steps` ×3) + `figure.figure-plate` (`.figure-plate__frame` svg `aria-hidden`, `.figure-plate__caption`) | static copy |
| 4 | Specialities band | `.band.reveal` › `.band__head` (rule/eyebrow/`h2#services-heading`/intro) + `ul.service-grid` → `partials/_speciality_card.html`; else `partials/_empty.html`; `.band__more` → `speciality_list` | `specialities` |
| 5 | Doctors band | `.band.band--tint.reveal#doctors[aria-labelledby=doctors-heading]` › `.band__head` + `ul.doctor-grid` → `partials/_doctor_card.html`; else `_empty`; `.band__more` → `doctor_list` | `doctors` |
| 6 | Closing CTA | `.band.cta-band.reveal` › `.cta-band__inner` (`h2#cta-heading`, `<p>`, `.hero__actions`: `btn--inverse` "Book an appointment" → `doctor_list`; `btn--secondary` "Create an account" → `accounts:register` when anonymous) | `user` |

### 4.3 CSS map (homepage-relevant, `static/css/styles.css`, 1842 lines) **[verified]**

| Lines | Rule(s) | Notes |
|-------|---------|-------|
| 581–658 | `.hero`, `.hero::before`, `.hero::after`, `.hero__grid`, `.hero h1`, `.hero__lead`, `.hero__actions`, `.hero .btn--secondary`, `.hero :focus-visible` | hero **carries the only gradient** + one dimensional layer (`.hero::after`) + texture (`.hero::before`) |
| 660–697 | `.hero__panel`, `.hero-badge` | panel has `--shadow-lg` |
| 1307–1365 | `.site-footer*` | footer chrome (shared, out of scope) |
| 1372–1375 | `.band`, `.band--tint`, `.band--compact` | band rhythm |
| 1380–1416 | `.section-rule`, `.eyebrow`, `.section-title`, `.section-intro`, `.band__head`, `.band__more` | the shared section-header grammar |
| 1419–1440 | `.trust-strip`, `.trust-item(+.trust-item)`, `.trust-value`, `.trust-label` | tabular real counts |
| 1443–1497 | `.about-grid`, `.about-copy p`, `.figure-plate(+__frame/__caption)`, `.about-steps(li::before, strong)` | about band + figure-plate (generic medical-cross/heartbeat SVG) |
| 1500–1547 | `.service-grid`, `.service-card(+hover/focus-within), __title/__text/__link` | shared card styles (partials-driven) |
| 1550–1619 | `.doctor-grid`, `.doctor-card(+hover/focus-within)`, `.avatar`, `__head/__name/__qual/__meta/__link` | shared card styles |
| 1622–1651 | `.cta-band`, `.cta-band__inner`, `.cta-band h2/p`, `.btn--secondary`, `.band--tint .empty` | closing CTA is a **solid brand surface (`#086063`) — already flat, no gradient** (**corrected by the H1 baseline**, §5) |
| 1696–1705 | `.js .reveal`, `.js .reveal.is-visible` | one-shot reveal |
| 1733–1736 | `@media (max-width:900px)` | hero grid collapses to 1 col |
| 1797–1805 | `@media (max-width:760px)` / `(max-width:640px)` | `.about-grid` 1 col, `.figure-plate{order:-1}` |
| 1818–1835 | `@media (prefers-reduced-motion: reduce)` | reveals shown instantly; hero animation off |

### 4.4 Shared partials (reuse; do not fork) **[verified]**

`templates/partials/_speciality_card.html` (`.service-card`),
`_doctor_card.html` (`.doctor-card`), `_empty.html`, `_field.html`,
`_form_errors.html`.

### 4.5 Known shared issue (document, do not fix here) **[verified]**

`templates/partials/_field.html` emits `aria-describedby="id_<field>_error"` under
Django 5.2 while no element carries a matching `id` (dangling reference). Out of scope for
the homepage; recorded so it is not mistaken for a homepage regression.

---

## 5. Reference-to-component mapping table

> "Reference device" = transferable grammar (§2.3). "Status" = whether the homepage
> already implements it. All mappings are **grammar only**; no asset/copy/font/CSS is
> carried across. **Rows marked ↺ were re-checked against the H1 baseline.**

| Reference device | Homepage component today | Status | Planned action |
|------------------|--------------------------|--------|----------------|
| Reusable section-header block (rule+label+serif H2+lede) | `.band__head` + `.section-rule`/`.eyebrow`/`.section-title`/`.section-intro` | **Partial** — About band lacks the `.band__head` wrapper | Normalise About to the same wrapper/rhythm (no contract change) — §10 H4 |
| Short rule above the label | `.section-rule` | **Done** | Tighten spacing consistency only |
| Captioned "figure plate" | `figure.figure-plate` + `.figure-plate__frame` svg + `.figure-plate__caption` | **Partial** — present but small & generic (generic clinic glyph) | **Promote to a dedicated, substantial visual section; make it photo-ready** — §7, §10 H2 |
| **Image-led visual moment (Hospic leads with photography)** | **none — no images in the repo** | **Missing** | **Add one dedicated visual section with an original SVG illustration (photo-ready slot)** — §7 |
| Large tabular numerals for real counts | `.trust-strip` / `.trust-value` | **Done** (`tabular-nums` verified) | Keep; no action |
| Genuine ordered sequence | `ol.about-steps` (`li::before` counters) | **Done** | Keep; verify numbering/contrast |
| Bands separated by rules + spacing | `.band` / `.band--tint` + `.section-rule` | **Done** | Keep; ensure tint/gradient restraint |
| Flat closing CTA | `.cta-band` | ↺ **Done** — already solid `#086063`, no gradient (plan assumption was wrong) | **Re-scoped:** no flattening needed; at most micro-polish — §10 H2 (dropped from H2) |
| Card grid idiom | `.service-grid`/`.doctor-grid` (shared partials) | **Done** | Reuse; **do not** fork partials |
| Hero with single dimensional element | `.hero` + `.hero::after` (the one dimensional layer) | **Done** | Keep as the single dimensional moment (see §7.2 on hero imagery) |

---

## 6. Proposed section hierarchy (when implemented)

Target order gains **one** new band (the dedicated visual section). Everything else keeps
its current position.

| # | Section | Notes |
|---|---------|-------|
| 1 | Hero | Unchanged composition; hero stays the single dimensional moment (§7.3). |
| 2 | At-a-glance | Conditional; real counts only. |
| **2b** | **Visual band (new — recommended)** | **Dedicated image-led section** — large original SVG illustration in a photo-ready plate + short honest caption/lede. Placement rationale in §7.3. |
| 3 | About band | Header normalised to `.band__head` (§10 H4); its inline figure is **consolidated into the visual section** (avoids two competing figures) — decision for review (§7.3). |
| 4 | Specialities band | `.band__head` + `service-grid` + `band__more`. |
| 5 | Doctors band | `.band--tint#doctors` + `band__head` + `doctor-grid` + `band__more`. |
| 6 | Closing CTA | Already flat; real links only. |
| 7 | Footer | Shared chrome — unchanged. |

---

## 6A. Dedicated visual section & imagery strategy (H1 review response)

> **This is the core of the revision.** It answers: *what* visual section, *what*
> image/illustration, *which files*, *how it behaves*, and *how we verify it*.

### 7.1 Why it is needed (problem statement) **[observed]**

- The repository has **no images at all** (0 raster files; 2 inline SVG data-URIs in the
  hero). **[observed]**
- The hero's visual treatment is a **decorative CSS pattern**, not a content-bearing image.
- The About `figure-plate` is a **generic medical-cross/heartbeat glyph** — it reads as a
  placeholder, not an identity. **[observed via template/CSS]**
- The speciality/doctor bands are text-led cards with monogram avatars (correctly so — no
  portraits allowed), so nothing on the page carries a substantial, purpose-made visual.
- **Net:** the page's visual identity rests on flat colour bands + a generic glyph — exactly
  what the H1 review flags.

### 7.2 Hero photograph vs custom illustration — evaluation **[inference]**

| Criterion | (A) Large clinic photograph in the hero | (B) Original custom illustration |
|-----------|------------------------------------------|----------------------------------|
| Asset available now? | **No** — no licensed clinic photo exists | **Yes** — authored in-repo, no external asset |
| Licensing | Requires written clinic consent + a licence record | **Original work; no licence required** |
| ADR-020 fit | OK if self-hosted, but adds binary + weight | **Ideal** — inline SVG, no download, no CDN |
- Risk of inventing facts | High (a "clinic photo" implies real people/place) | **Low** — abstract/editorial, no clinical claims |
| Conflicts with page rules | Competes with `.hero__panel` form; risks a **second** dimensional element | Flat 2D; keeps the **single** dimensional rule |
| CLS/perf risk | Must reserve space; heavier bytes | SVG scales; reserve via `aspect-ratio` |
| Verdict | **Not now** — keep as a **photo-ready slot** | **Recommended now** |

**Decision:** build the dedicated visual section around a **custom, hand-authored,
self-hosted SVG editorial illustration** (no external asset). Structure it inside a
**photo-ready figure plate** so an **approved, licensed clinic photograph** can replace the
illustration later **with no markup change** (swap the partial's parameters).

**Answering "hero photo or illustration":** *neither a hero photograph nor a hero
illustration is added.* The hero keeps its single dimensional moment and the real booking
panel; the **substantial visual lives in the dedicated section** where it does not compete
with the form. (If the user later prefers an in-hero image, that is a separate decision that
would require retiring the `.hero::after` dimensional layer to preserve the one-element
rule.)

### 7.2.1 Art-direction brief (so it is not "generic clip-art")

The critique explicitly warns against generic placeholder illustrations. The illustration
must be **compositional and editorial**, not a lone glyph:

- **Subject:** an abstract, product-true scene — e.g. a considered "appointment-flow"
  composition (a scheduling/wayfinding motif: a stylised week grid, time ticks, and a
  card-like "slot" shape) rather than a stethoscope/heart/heartbeat cliché.
- **Style:** flat, two-tone + accent (brand teal `#0b7c80` / soft `#e8f8f8` / ink), hairline
  strokes, generous negative space, subtle geometric rhythm — matching the "Modern Medical
  Journal" grammar.
- **Consistency:** uses the existing palette tokens only; no new colours, no gradients, no
  glassmorphism, no web fonts, no external files.
- **Truthfulness:** the illustration depicts the **product** (booking/scheduling), never
  invented clinical imagery, doctor likenesses, patient scenes, accreditation logos, or
  claims. It is **decorative** (`aria-hidden`), with meaning carried by real caption text.
- **Form:** authored as an inline `<svg>` inside a partial (no binary asset) with a
  `viewBox` and `preserveAspectRatio="xMidYMid slice"`, matching the existing figure-plate
  approach (`home.html:100–108`).

### 7.3 Location & fit in the page structure

**Recommended placement: a new `section.band.band--viz` between the trust strip (band 2)
and the About band (band 3).** Rationale:

- It introduces a **substantial image-led moment early**, before the text-heavy bands —
  directly answering the review.
- It sits on a **plain (white) band** so the tint rhythm stays intact (tint at About and
  Doctors) — bands remain separated by rules + spacing, per §2.3.
- It does **not** disturb the section-header grammar or any contract id/anchor.
- **Consolidation:** the About band's current small `figure-plate` is **moved into** this
  section (enlarged, photo-ready) so the page has **one** strong visual rather than two
  similar figures; About keeps only its heading + copy + 3-step list. *(Decision for review
  — see §12 Q5. Alternative: keep the About figure and place the new section after About.)*

**Rejected alternatives [inference]:**
- *Hero enlargement:* crowds the real booking panel and risks a second dimensional element.
- *Image in the Doctors band:* would imply doctor portraits / invented identities (§12 Q4).
- *A full-bleed photo strip:* no licensed photography exists; would require invented imagery.

### 7.4 Image source & licensing requirements (non-negotiable)

**Preferred (target state):** **approved, clinic-supplied photographs**, self-hosted under
`static/img/home/`, with a licensing record.

**Now (this plan):** an **original SVG illustration authored in-repo** — no external asset,
no licence needed, ADR-020-compliant (no CDN, no build, no web font).

**Prohibited without exception:**
- **Hotlinking or copying** any Hospic / reference image, video, SVG or illustration.
- **Unlicensed stock photography**, or any asset without a documented licence.
- **Invented clinic photographs**, fabricated interiors, or AI-generated "patients".
- **Doctor portraits / likenesses** (the spec §G and §J forbid fake identities; avatars stay
  initial-based).
- **Medical claims encoded in imagery** (awards, accreditations, "24/7", equipment claims).

**Asset hygiene (if/when real photos are added):** self-host only; explicit `width`/`height`
or `aspect-ratio` (reserve space, low CLS); `loading="lazy"` below the fold; `srcset` for
responsive sizes; correct `alt` (empty/`aria-hidden` if purely decorative); a licensing
manifest (see §9.6) recording **filename · source · licence · date · alt text**.

### 7.5 Responsive behaviour

| Width | Layout | Illustration | Caption |
|-------|--------|--------------|---------|
| **≥1024** | 2-column within `.container` (visual ~60% / caption-rail ~40%) | photo-ready frame, `aspect-ratio` ~`3/2` | right rail: serif lede + short honest caption |
| **768** | 1 column (illustration first) | full-width, `aspect-ratio` ~`16/9` | below the illustration |
| **390** | 1 column | full-width, `aspect-ratio` ~`4/3` | below; text max-width = `--measure-body` |

Rules: **reserve space** via `aspect-ratio` (no CLS); **no horizontal overflow**; the motif
stays `aria-hidden`; caption is real text; **reduced-motion**: no motion at all; **JS off**:
fully visible (the section is never behind `.reveal` for content — if `.reveal` is used,
the existing JS-off safety applies). (Existing behaviour: `.reveal` content is visible
without JS; see `styles.css:1696`.)

### 7.6 How we will verify the result visually

- **Computed geometry at 390 / 768 / 1024 / 1440** (headless Chrome, offline rolled-back
  test-client recipe or a fresh server): overflow `0`; section present exactly once;
  illustration frame has a **stable `aspect-ratio`** and **non-zero reserved height**;
  caption contrast ≥ AA; one `h1`; heading order preserved.
- **Asset integrity:** grep confirms **no external host** in `src`/`url()` (no hotlinks);
  if a real image is used, assert `width`/`height` (or `aspect-ratio`) and `alt` presence.
- **Accessibility:** decorative SVG is `aria-hidden`; caption is real text; focus order
  unaffected; reduced-motion pass static; no-JS pass shows the section.
- **Screenshots** captured at the four widths for the human reviewer.
- **Caveat (updated 2026-10-18):** screenshots **are** now reviewed whenever captured
  (image reading works — see the §3 note); quantitative geometry + DOM/HTML inspection
  remains the objective backbone, and screenshots are still provided for the reviewer's
  final aesthetic judgement.

---

## 6B. Project-wide photography strategy (Revision 3)

> **Added 2026-10-18 per user review. Planning only — nothing implemented.** The former
> single-photo H7 is superseded by this section: a route-by-route imagery inventory, a
> proposed local asset structure, a phased implementation proposal (IMG-P1...IMG-P5), and
> the approvals required before any imagery work begins.

### 6B.1 Brief and non-negotiable constraints

The approved direction is a **photo-rich, Hospic-inspired experience** — every major
section led by deliberate imagery — within these binding constraints:

- **Honesty first.** Stock photography is used as **atmosphere/illustration only**, never
  presented as "our doctors", "our staff", "our facility", or real patient stories.
  Doctor portraits may only represent **real doctors** and require per-doctor approval;
  the initial-based avatar remains the fallback whenever no approved photo exists.
- **Licensing.** Every image is self-owned: licensed source, stored locally, recorded in
  a per-asset manifest (`docs/imagery-licensing.md`). No copying or hotlinking of Hospic
  or any reference asset (§7.4). Unlicensed assets are prohibited.
- **Technology (ADR-020).** Self-hosted images under `static/` only; no CDN, no build
  step, no lazy-load JS library; Django server-rendered templates + hand-built CSS.
- **Transactional restraint.** Booking, appointment management, dashboards and
  doctor self-service pages keep their workflows clear: **no large decorative
  photography inside forms, tables or stacks**; at most a restrained panel/banner
  treatment if approved.
- **Continuity.** The teal palette, editorial typography, responsive/a11y/reduced-motion
  rules and all Django contracts (spec §K) are unchanged by imagery work.
- **Recorded conflict with the spec:** `docs/frontend-design-specification.md` §G currently
  prefers CSS/SVG-only illustration. The illustration preference is superseded by this
  user decision; the **fake-identity prohibitions of §G/§J remain fully in force**.

### 6B.2 Route-by-route image inventory (verified 2026-10-18)

All templates/routes verified from `config/urls.py`, app `urls.py` files and the template
tree. "Level" is the proposed imagery intensity.

| Route | Template(s) | Imagery candidate | Level |
|-------|-------------|-------------------|-------|
| `home` | `templates/home.html` | Hero panel, dedicated visual band (`.band--viz` section, H2 loop via `templates/partials/_figure_plate.html`), speciality-card tiles, doctor cards, optional behind-CTA | **Rich** (H2 already has `band--viz`) |
| `speciality_list` | `website/templates/website/speciality_list.html` | Per-speciality tile imagery on the card grid (illustration-first or stock, where honest) | Moderate illustrated |
| `speciality_detail` | `website/templates/website/speciality_detail.html` | Restrained header visual per speciality; doctors grid as today | Moderate |
| `doctor_list` | `website/templates/website/doctor_list.html` | Filter bar + cards; **portraits only for real doctors** (with approval); no decorative photos elsewhere | Moderate |
| `doctor_detail` | `website/templates/website/doctor_detail.html` | Profile header / side visual + real-doctor portrait next to bio | Moderate |
| `accounts:login`, `accounts:register`, `accounts:logged_out` | `accounts/templates/accounts/*` | One shared calm panel visual beside the auth panel (optional; forms stay primary) | Restrained |
| `password_reset_form/done/confirm/complete` | `accounts/templates/accounts/*` | Same shared auth-side visual treatment (or none) | Restrained |
| `appointments:book`, `appointments:detail`, `appointments:list`, `appointments:cancel`, `appointments:reschedule` | `appointments/templates/appointments/*` | **No decorative photos.** Booking/management forms stay clean; at most micro-illustration if approved later | None (restraint by design) |
| `dashboards:landing/patient/doctor/receptionist/receptionist_book/admin/appointment_status` | `dashboards/templates/dashboards/*` | **No photos** — data-first surfaces; colours/typography carry the brand | None |
| `clinic:availability_*`, `clinic:leave_*` | `clinic/templates/clinic/*` | **No photos** — doctor self-service forms/tables | None |

Shared partials touched by imagery: `templates/partials/_figure_plate.html` (already
param-driven), `_doctor_card.html` (initial avatar currently), `_speciality_card.html`,
`templates/base.html` (footer chrome untouched). One pass through the partial updates
every listing page.

### 6B.3 Data & asset reality (verified)

- Repository still contains **0 image files**; no `MEDIA` config — imagery must live in
  `static/` and needs no settings change.
- **Real slugs** (queried from sqlite via `manage.py shell`, 2026-10-18):
  - Specialities (5): `cardiology`, `dermatology`, `general-medicine`, `orthopaedics`,
    `paediatrics`.
  - Doctors (3): `aswin-kumar` (Cardiology), `meera-nair` (Dermatology),
    `rahul-verma` (General Medicine).
- The `Doctor` model has **no `profile_image` field** (ADR-015: no image pipeline, no
  Pillow; "revisit only if the employer requests photos") and no `is_active` field — the
  public gate is `is_accepting_appointments`.

### 6B.4 Asset directory & manifest structure (proposal)

```
static/img/
  home/            band--viz / hero (only if approved) — e.g. home-visual-1200/800/480 variants
  specialities/    <slug>-card.webp (+ smaller variants) for each of the 5 real slugs
  doctors/         <slug>-profile.webp (+ variants) for consenting real doctors
  ui/auth/         shared auth-side panel visual (if approved)
docs/imagery-licensing.md
```

Per-asset manifest row: `filename | source | licence (+type) | acquired | photographer | alt text | where used`.

Implementation rules for any photo:
- Reserved space via `aspect-ratio`/explicit `width`+`height` (no CLS); `loading="lazy"`
  below the fold; `decoding="async"`; worded alt text (empty `alt=""` only when purely
  decorative).
- WebP preferred with JPEG/PNG fallback (via `<picture>` if IMG-P1 extends
  `_figure_plate.html` accordingly); per-image weight budget (target ≤ ~150 KB at display
  width; hero ≤ ~250 KB) — budget proposal, confirm with the reviewer.
- Aspect ratios per spec §G: card thumbs 1:1 or 4:3; profile/portrait 1:1; wide band ~3:2.

Portraits without model changes (recommended now): **filename convention** keyed by the
verified real slugs — `static/img/doctors/<slug>-profile.webp` rendered when present,
initial avatar otherwise. Zero model/migration change; honours ADR-015 today. (A real
`Doctor.profile_image` field would need a model+migration phase and explicit new
approval — see §6B.6 item 7.)

### 6B.5 Phased implementation proposal (dependencies vs H3-H6)

| Phase | Scope | Files | Independence / verification |
|-------|-------|-------|-----------------------------|
| **IMG-P0** | Approvals + sourcing (human task): photos from the clinic, or licensed stock acquisition decisions; draft `docs/imagery-licensing.md` rows | `docs/imagery-licensing.md` only | No app code. Blocks everything below. |
| **IMG-P1** | Imagery infrastructure: create `static/img/` tree; extend `_figure_plate.html` (`<picture>`/`srcset`/variants + graceful missing-image behaviour) and the initial-avatar fallback in `_doctor_card.html` | `templates/partials/_figure_plate.html`, `templates/partials/_doctor_card.html`, `static/css/styles.css`, `docs/imagery-licensing.md` | No-CLS checks; missing-photo fallback verified; website tests green |
| **IMG-P2** | Homepage imagery: speciality-card tiles; `band--viz`/hero photo swap via `image_url` params **only if approved**; doctor cards stay initials until portraits approved | `templates/home.html`, `templates/partials/_speciality_card.html`, `static/img/**` | 4-width geometry (as §9.3); tests green; manifest complete |
| **IMG-P3** | Public website pages: speciality list/detail tiles, doctor list/detail portraits + doctor_detail visual | `website/templates/website/*`, `static/img/**` | Same per-page QA; §K.5 strings intact |
| **IMG-P4** | Accounts restraint pass: optional shared auth-side visual | `accounts/templates/accounts/*` | Forms-first QA; contrast AA |
| **IMG-P5** | Restrained surfaces audit (appointments/dashboards/clinic): confirm no photos; code change only if a restrained treatment is explicitly approved | none expected | QA-only pass |

**Ordering.** H3 completes first (it is paused mid-flight); then H4-H6 close the homepage
phases, then imagery phases run in order. Interleaving earlier than H4 is not
recommended (both the H phases and IMG phases touch the same shared partials and CSS).

### 6B.6 Approvals required before any imagery phase starts

1. **Clinic-produced photographs** — do they exist (waiting areas, exteriors, care
   teams, equipment) and may they be used as true "our clinic" imagery? Written
   consent/licence per asset.
2. **Licensed stock** (if clinic photography is insufficient) — which marketplace(s) the
   clinic will purchase from (e.g. Adobe Stock / Getty / licence-permitted options), and
   who acquires/pays. Extended/wide web-use licence per asset; nothing copied or
   hotlinked from Hospic.
3. **Atmosphere usage OK** — explicit confirmation that generic healthcare stock may
   appear without implying "our facility/staff", with carefully worded captions/alt.
4. **Doctor portraits** — for Aswin Kumar, Meera Nair, Rahul Verma only: clinic-supplied,
   consented portraits? **Stock portraits may never stand in for real doctors.**
   Initials avatars remain the fallback.
5. **Speciality tiles** — in-repo SVG illustration first (needs no approval), licensed
   stock only where honest (needs item 2 approval).
6. **Auth-side visual** — one shared calm image, or none?
7. **Model field** — should a `Doctor.profile_image` phase ever be added (ADR-015
   revisit, needs model+migration approval), or is the filename convention (§6B.4)
   permanent?

---

## 7. Out-of-scope elements and reasons

| Element | Reason excluded |
|---------|-----------------|
| Rating badge (e.g. 4.9/5) | Requires data the clinic does not have — unverifiable claim. |
| Health packages / pricing grid | No pricing data / commercial module. |
| Testimonials / quotes | Invented or unlicensed copy; no source of truth. |
| Blog / "latest health insights" | No blog model or content. |
| FAQ accordion | No FAQ model; would be invented content. |
| Opening hours, address, phone, email, social links | Not in the data model; inventing them is prohibited. |
| "Years of excellence", patient counts, satisfaction %, "advanced technology" | Invented statistics/claims. |
| **Reference (Hospic) images / video / SVG / brand** | **Unlicensed; must not be hotlinked or copied (§7.4).** |
| **~~Doctor portraits / patient photos / clinic-interior photos~~** *(updated by Rev 3)* | **Invented identities/claims remain prohibited**; real-doctor portraits and clinic-owned imagery are now *planned candidates* under the §6B truthfulness/licensing rules (atmosphere stock never presented as "our" people/place; portraits only via per-doctor approval). |
| **A second dimensional/gradient hero layer** | Only **one** dimensional element is approved (`.hero::after`); the visual section is flat 2-D. |
| Lenis/GSAP/Three.js/Framer runtime, smooth scroll | ADR-020; not added. |
| Web fonts / CDN assets | ADR-020; not added. |
| Changes to URL names, context vars, form fields, permissions, booking logic | Binding contracts (spec §K). |
| Fixing `_field.html` dangling `aria-describedby` | Shared partial, separate concern; documented in §4.5 only. |
| New models/routes/apps/dependencies/migrations | Out of architecture. |

---

## 8. File-by-file implementation plan

> When approved. **Inspection-only right now.** No file listed here was modified to
> produce this document.

### 8.1 `templates/partials/_figure_plate.html` (new, photo-ready)
- A **reusable** partial that renders a **photo-ready figure plate**:
  - if an `image_url` (+ `alt`) is supplied → `<img>` with explicit `width`/`height`
    (or `aspect-ratio`), `loading="lazy"` when below the fold, and the given `alt`;
  - otherwise → the **original inline SVG illustration** with `aria-hidden="true"`.
  - Always renders a **real caption** (`figcaption`) — meaning is in text, never only the
    image.
- Params (proposed): `illustration` (variant key), `caption`, optional `image_url`,
  `image_alt`, `width`, `height`, `loading`.

### 8.1 `templates/home.html`
- **New section** `section.band.band--viz.reveal` between the trust strip (L46–65) and the
  About band (L67): `h2` (section heading, real text) + `{% include "partials/_figure_plate.html" %}`.
- **About band (lines 67–116):** (recommended) remove the inline `figure.figure-plate` and
  keep the heading + `<p>`s + `ol.about-steps`; **keep** `h2#about-heading`. (Also wrap the
  About header in the shared `.band__head` markup — §10 H4.)
- **Keep unchanged:** hero, trust strip, service/doctor grids, closing CTA; all ids,
  anchors (`#doctors`), `get_absolute_url` links and the hero form `GET → doctor_list`.
- **Rule:** no invented content; keep exactly one `h1`.

### 7.5 `static/css/styles.css`
- **Add** `.band--viz`, `.figure-plate--lg` (+ `__frame`/`__caption`), a 2-col grid + a
  1-col ≤900 stack, `aspect-ratio` on the frame, and responsive rules. **Tokens only** — no
  new colour/font/motion tokens.
- **Figure plate (1453–1468):** support a **large** variant with a consistent
  `aspect-ratio` across widths.
- **`.doctor-card__qual` (~1597):** raise contrast `#6b7280` → `#4b5563` on the tint band
  (H1 baseline measured **4.42:1**, below AA) — §10 H3.
- **`.cta-band` (1622–1649):** **no flattening needed** (already solid `#086063`); optional
  micro-polish only (re-scoped §10 H2).
- **`.trust-value` (1433):** already `tabular-nums` — confirm only.
- **`.eyebrow` (1392):** keep or remove per decision §12 Q3.
- **Reveal (1696–1705) and reduced-motion (1818–1835):** unchanged; the new section must be
  neutral under reduced-motion.
- **Rule:** tokens only; no framework; no CDN; no web fonts.

### 7.3 `static/js/app.js`
- **No change expected.** Reveals and mobile nav already exist. If a phase needs no JS, do
  not touch it.

### 7.4 Tests — `website/tests.py`
- Add assertions that the homepage (a) returns 200, (b) renders an active speciality name
  (§K.5), (c) has exactly one `h1`, (d) contains the new dedicated visual section exactly
  once, (e) keeps the `#doctors` anchor and `doctor_list` CTA targets, (f) keeps
  `accounts:register` CTA only for anonymous users, (g) renders the `trust-strip` only when
  counts exist. **Additive only** — do not weaken existing tests.

### 7.5 Docs
- `docs/imagery-licensing.md` (new, when a real photo is added): filename · source · licence
  · date · alt text. Until then, §7.4 records "original SVG, licence: in-repo" .
- After each phase, add a short report `docs/phase-7.5-homepage-<phase>-report.md`.

---

## 8. Ordered phases (each independently testable & reviewable)

> **Reassessment:** the original **H2 ("flatten the closing CTA band") is void** — the H1
> baseline proved `.cta-band` is already flat (`#086063`, no gradient). **H2 is re-scoped to
> the dedicated visual section.** H1 (baseline) is complete.

| Phase | Scope | Files | Independently testable by |
|-------|-------|-------|---------------------------|
| **H1** ✔ done | Baseline inspection (no code) | — | `docs/homepage-h1-baseline-report.md` |
| **H2** | **Dedicated visual section** — new `_figure_plate.html` partial (photo-ready) + new `.band--viz` section with the original SVG illustration; consolidate the About figure into it | `templates/partials/_figure_plate.html`, `templates/home.html`, `static/css/styles.css` | Section present once; overflow 0 at 4 widths; stable `aspect-ratio`; caption is real text; motif `aria-hidden`; one `h1`; no external host in `src` |
| **H3** | Card/meta polish — **fix `.doctor-card__qual` contrast** (4.42 → ≥4.5); verify `.trust-value` tabular-nums; figure-plate aspect normalisation | `static/css/styles.css` | Contrast ≥ AA at 4 widths; no other card regression (website tests green) |
| **H4** | Section rhythm + **About header → `.band__head` grammar** (the original plan-H1 change) | `templates/home.html`, `static/css/styles.css` | `.band__head` count = 3; `#about-heading` present; spacing consistent; no overflow |
| **H5** | Focus-state + responsive sanity for homepage interactive elements | `static/css/styles.css` | `:focus-visible` visible on CTAs/select; touch targets ≥44px on mobile |
| **H6** | Homepage contract tests + phase reports | `website/tests.py`, `docs/` | `manage.py test`, `pytest` green; reports written |
| **H7** *(superseded by Revision 3; batch 1 executed early per user instruction of 2026-10-18)* | **Project-wide imagery phases IMG-P0...IMG-P5 (§6B.5)** — the single-photo swap folds into IMG-P2; **batch 1 (hero + About + speciality tiles) implemented before H3-H6 per user decision**, see `docs/phase-7.5-homepage-imagery-batch-1-report.md` | `templates/partials/_figure_plate.html`, `templates/partials/_speciality_card.html`, `website/templatetags/clinic_images.py`, `templates/home.html`, `static/css/styles.css`, `static/img/**`, `docs/imagery-licensing.md` | Per-phase verification columns in §6B.5; batch 1 verified in its report |

Each phase must finish with the full verification block (§11) before the next begins.
**Do not auto-advance** — stop for review after each.

---

## 9. Acceptance criteria + validation commands

### 11.1 Acceptance criteria (plan-level)

- [ ] Home returns **200**; an **active speciality's name still renders** (§K.5).
- [ ] **Exactly one `h1`**; heading order preserved.
- [ ] **One dedicated visual section** exists, image-led (not a flat colour block), with a
      **stable `aspect-ratio`** and a real-text caption.
- [ ] The illustration is an **original in-repo SVG** (no external file); **no hotlink/copy**
      of any reference asset; **no invented photographs/portraits**.
- [ ] Section-header grammar **consistent** across the labelled bands.
- [ ] Trust strip shows **only real counts**; numerals tabular; **no invented metric**.
- [ ] Closing CTA is **flat**, real links only; `doctor_list` always; `accounts:register`
      only for anonymous users.
- [ ] **No horizontal overflow** at **390 / 768 / 1024 / 1440 px**.
- [ ] **Contrast ≥ WCAG AA** for all text (incl. `.doctor-card__qual` on tint).
- [ ] **Interactive targets ≥ 44 px** (pointer + touch).
- [ ] **Reduced motion:** every transition neutralised; the visual section is static.
- [ ] **JS off:** all content visible (nothing hidden behind `.reveal`).
- [ ] **No change** to URL names, context vars, form fields, permissions, booking logic.
- [ ] **No** new dependency, CDN, web font, framework or build step; **no** new MEDIA config.

### 11.2 Validation commands

```
python manage.py check
python manage.py makemigrations --check --dry-run      # expect "No changes detected"
python manage.py test                                  # large timeout (>= 600000 ms)
pytest -q                                              # large timeout (>= 600000 ms)
git diff --check                                       # clean (benign CRLF notices only)
```

### 11.3 Browser / responsive checks (per phase touching CSS)

- Headless Chrome (a fresh server, or the offline rolled-back test-client recipe).
- For `/` at **390 / 768 / 1024 / 1440 px**: `scrollWidth <= clientWidth` (no overflow);
  exactly one `h1`; zero console errors; no low-contrast text.
- **Imagery checks:** the visual section's frame has non-zero reserved height and a stable
  `aspect-ratio`; decorative SVG is `aria-hidden`; caption is real text; **no external host**
  appears in `src`/`url()`; if a real image is present, `width`/`height` (or `aspect-ratio`)
  and `alt` are set.
- One **reduced-motion** pass and one **no-JS** pass on `/`.
- Confirm nav, hero CTA, `#doctors` anchor and closing CTA targets resolve.
- **Tooling caveat:** the assistant cannot inspect images; only quantitative results are
  reported, and no screenshot critique is claimed unless screenshots were captured and
  actually reviewed (see the End report).

---

## 10. Risks, dependencies & unresolved questions

| # | Risk / question | Mitigation / status |
|---|-----------------|---------------------|
| R1 | **Larch Health prototype missing** — brief named it explicitly | Substituted Hospic per user choice; recorded in §2.0. **Unresolved:** confirm before implementing. |
| R2 | ~~Model cannot read images~~ **Resolved 2026-10-18** — image reading is supported; H2 band screenshots were genuinely reviewed. Verification stays dual: quantitative geometry + screenshot review. |
| R3 | **No licensed photography** | Ship an **original SVG** now; keep a **photo-ready slot** (H7) for approved photos (§7.4). (Rev 3: superseded by §6B phases; slot logic unchanged.) |
| R4 | Content truthfulness | Real data only; illustration depicts the **product**, never clinical claims (§7.2.1). |
| R5 | **Illustration reads as generic clip-art** (the review's warning) | Follow the art-direction brief (§7.2.1); review the rendered result before H3. |
| R6 | **CLS / layout shift** when an image is added later | Reserve space via `aspect-ratio` + explicit dimensions (§7.5). |
| R7 | Restyling breaks the booking contract | Phases restricted to home/CSS; tests assert URL/context targets (§7.4). |
| R8 | Bootstrap-5 wording vs **ADR-020** | Follow ADR-020 (hand-built CSS). Open conflict — needs user confirmation. |
| R9 | Long test runtime vs shell timeout | Run with an explicit large timeout. |
| R10 | Changing shared partials affects other pages | Homepage phases must **not** fork shared card partials. |
| R11 | MySQL/InnoDB validation not performed (ADR-003) | SQLite-only locally; the 1 skip is MySQL-only (`appointments/tests.py:764`). |
| R12 | Preserving uncommitted work | No `git reset/checkout/clean`; edits only. |
| R13 | **Licensing integrity for project-wide imagery** | Clinically-owned photos with written consent, or purchased licences with per-asset manifest rows (§6B.4); never copied/hotlinked from Hospic; no asset without a documented licence. |
| R14 | **Stock imagery read as "real" clinic/staff** | Honesty rules (§6B.1): atmosphere only, carefully worded captions/alt; **never** claim stock as our people/place; real-doctor portraits only with per-doctor approval. |
| R15 | **Doctor portraits have no model field** (ADR-015) | Filename convention keyed by real slugs (§6B.4) — zero model change; a `Doctor.profile_image` field would be a separate approved phase (§6B.6 item 7). |

**Unresolved questions for the user:**
1. Is a **Larch Health** prototype available anywhere (vs the Hospic substitute)?
2. Confirm **ADR-020** takes precedence over "Bootstrap 5" in any integration prompt.
3. Should the ALL-CAPS `.eyebrow` label be **kept** or **removed**? (spec D4, open)
4. Confirm **no doctor portraits / patient photos** are to be introduced (this plan assumes
   none — initial avatars only). *(Revised by Revision 3: real-doctor portraits are now
   conditionally planned — see §6B; the honesty rule stands.)*
5. **Placement decision (H2):** (a) new visual band **between trust and About** and
   **consolidate** the About figure into it *(recommended)*, or (b) keep the About figure and
   place the new section **after About**?
6. Does the clinic have an **approved, licensed photograph** (or plan to supply one)? If
   yes, H7 can be pulled forward; if no, the SVG illustration is the permanent visual.
7. Confirm no new medical/pricing/testimonial content is to be introduced (this plan assumes
   not).
8. **Photography/imagery approvals (Revision 3):** the full decision list — clinic photos,
   licensed stock sources, atmosphere usage, doctor portraits, speciality tiles, auth-side
   visual, and the optional `Doctor.profile_image` model field — is consolidated in
   **§6B.6**. No imagery phase starts until those are answered.

---

## 11. Explicit confirmation — no app code changed

**To produce this document, no application code, CSS, HTML, template, JavaScript, model,
view, URL, setting, migration or dependency was created, edited or deleted.** The only file
written is this plan: `docs/homepage-reference-analysis-and-execution-plan.md`. Nothing was
staged, committed or pushed; no destructive git command was run.

---

## End report

**Trigger:** H1 review feedback — *"add a dedicated visual section"*; update the plan;
inspection and planning only.

**Docs inspected (this revision)**
- `docs/homepage-reference-analysis-and-execution-plan.md` (re-read in full).
- `docs/frontend-design-specification.md` (§E content rules, §G imagery, §J honesty,
  §K contracts).
- `docs/phase-7.5-implementation-plan.md` (baseline + verification method).
- `docs/hospic-reference-analysis.md`, `docs/hospic-to-care-clinic-implementation-plan.md`,
  `docs/animation-reference-analysis.md`, `docs/homepage-h1-baseline-report.md`.

**Homepage files / assets inspected (read-only)**
- `templates/home.html`, `templates/base.html`,
  `templates/partials/{_speciality_card,_doctor_card,_empty}.html`.
- `static/css/styles.css` (hero L581–697; figure-plate L1453; cta-band L1622–1651;
  reveal L1696; reduced-motion L1818).
- `static/js/app.js`; `website/views.py`; `website/urls.py`; `config/urls.py`;
  `config/settings/base.py` (no `MEDIA` config).
- **Asset audit:** `static/` contains **only** `css/styles.css` + `js/app.js`; **0 image
  files** repo-wide; the only `url(...)` assets are 2 inline SVG data-URIs (hero).

**What changed in the plan (revision)**
- Added **§6A (7.1–7.6): the dedicated visual section & imagery strategy** — including the
  hero-photo-vs-illustration evaluation, placement, licensing rules, responsive table, and
  verification.
- **Re-scoped H2** (CTA flattening is moot) → **H2 = dedicated visual section**; added
  deferred **H7** (licensed-photo swap).
- Corrected the CTA gradient assumption (§4.3, §5) and the `.trust-value` tabular-nums
  action (§5).
- Added imagery to §7 exclusions, §8 file-by-file, §9 acceptance, §10 risks, and the
  unresolved-questions list (§10 Q4–Q6).

**No-modification confirmation**
- No application code/CSS/HTML/JS/model/view/URL/settings/dependency changed. **No**
  stage/commit/push. H2 was **not** started.

**Git status**
- **Before revision:** identical to the H1 baseline state (40 pre-existing `M` files;
  untracked `docs/*`, `static/js/`, `templates/partials/`, `.agents/`; nothing staged).
- **After:** identical, **plus** this updated plan file (already untracked). No other change.

**Limitations**
1. **Larch Health prototype unavailable** → §2/§3 use Hospic (user-approved).
2. ~~**Cannot read images** → screenshots located, not visually analysed~~ — **superseded
   2026-10-18:** image reading is supported; H2 phase screenshots were genuinely
   visually reviewed (see the §3 note). The zero-image audit remains the structural
   corroboration for the original "no visual section" claim.
- 3. **No live reference run** → Framer motion timings remain **[not verified]**.
4. **MySQL/InnoDB** unvalidated locally (ADR-003).
- All plan content is a **proposal**; nothing has been implemented.

---

**Revision 3 report (2026-10-18 — project-wide photography strategy; planning only)**

**Inputs read/queried for this revision**
- `docs/frontend-design-specification.md` (read in full — §G imagery, §J honesty,
  §K contracts, §E page map, §F template inventory were the key inputs).
- `docs/architecture.md`, `docs/frontend-technology-and-skills-audit.md` (both read
  2026-10-18), plan Revision 2, H2 report (`docs/phase-7.5-homepage-h2-report.md`).
- Route/template inventory verified from `config/urls.py` + app `urls.py` files and the
  template tree (all `accounts/appointments/dashboards/clinic/website` page templates
  enumerated).
- SLUG query via `manage.py shell` (sqlite): 5 specialities
  (cardiology, dermatology, general-medicine, orthopaedics, paediatrics) and 3 doctors
  (aswin-kumar/Cardiology, meera-nair/Dermatology, rahul-verma/General Medicine); the
  `Doctor` model verified to have **no** `profile_image`/`is_active` fields (gates:
  `is_accepting_appointments`, ADR-015).

**What changed in the plan (Revision 3)**
- Added **§6B** on the project-wide photography strategy: constraints (§6B.1), the
  route-by-route image inventory (§6B.2), data/asset reality (§6B.3), asset directory and
  `docs/imagery-licensing.md` manifest structure (§6B.4), phased proposal IMG-P0...IMG-P5
  with ordering after H3-H6 (§6B.5), and the approvals checklist (§6B.6).
- **H7 is superseded** by IMG-P0...IMG-P5 (single-photo swap folds into IMG-P2) — phase
  table H7 row updated to point at §6B.
- Updated the assumptions that aged: the "assistant cannot read images" claims (§3 note,
  §7.6 caveat, R2, End-report limitation 2) are corrected — the H2 screenshots were
  genuinely reviewed; the §7 "doctor portraits" exclusion row now carries the Rev 3
  nuance (invented identities remain prohibited; real-doctor portraits are conditionally
  planned); Q4 annotated; Q8 (imagery approvals) added; risks R13-R15 added; a snapshot
  note added above §4.2 (home.html is now 180 lines post-H2).
- Deliverables of this revision: §6B plan + inventory + directory structure + phased
  proposal + approvals list. **No implementation deliverables**: no template/CSS/JS/asset
  changes, no downloads, no H3 resumption.

**No-modification confirmation (Revision 3)**
- No application code, CSS, HTML, JS, asset, model, URL or settings change. The only
  edited file is this plan. Nothing staged/committed/pushed; no destructive git action.

**Current working-tree state (as of this revision)**
- H2 complete/approved (see its report); H3 partial: only the
  `.doctor-card__qual` contrast edit in `static/css/styles.css` (`#6b7280` → `--ink-600`,
  computed 6.91:1 on tint / 7.56:1 on white); its test suite run was **aborted** by the
  user and remains outstanding. Everything else is untouched.

**Outstanding before anything is built**
- Human review of §6B (especially §6B.6 approvals 1-7); explicit approval to (a) finish
  and verify H3, (b) proceed H4-H6, (c) start IMG-P0/P1.
