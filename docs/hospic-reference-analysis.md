# Hospic Reference Analysis

> Scope: analyse the newly provided **Hospic** Framer template export as a *design
> reference only*, extract the transferable layout / typography / motion patterns, and
> record what must **not** be carried across into Care_Clinic. This document is
> evidence-led: every claim is tagged **[verified]**, **[inference]**, or
> **[not verified]** so it is never mistaken for a fact we did not actually check.
>
> Companion document: `docs/hospic-to-care-clinic-implementation-plan.md`.

---

## 0. Method & evidence basis

- The export is a **byte-for-byte Framer site copied into a Next.js shell**. Its
  `README.md` states plainly: *"What this is not: Source you can edit."* The Framer
  runtime (`*.mjs` chunks) renders the real markup client-side; the static HTML we read
  is the pre-rendered snapshot.
- The live reference site is hosted at `lower-circumstances-836286.framer.app`.
- **This analysis did not run the live site or the Framer runtime.** Motion timings,
  easing families and interactive behaviour are read from the serialized
  `__framer__*` data attributes and CSS, not from execution. Anything requiring a
  running browser is marked **[not verified]**.
- **No Hospic asset (image, video, font, SVG file, copy) is copied into Care_Clinic.**
  Hospic is a commercial template; the licence basis for reuse is absent (see §6).

### 0.1 Export inventory [verified]

- Location: `C:\Users\Ramprasad\Downloads\hospic-hospital-healthcare-framer-template-copy-exact-next`
- Shape: Next.js app whose `next.config.mjs` **rewrites** every route to a static
  `public/**/*.html` snapshot. `app/layout.tsx` (272 B) and `app/page.tsx` (411 B) are
  placeholders; the real pages are the snapshots.
- Routes (3): `/` → `public/index.html` (924,436 B); `/about` → `public/about/index.html`
  (471,216 B); `/pricing` → `public/pricing/index.html` (450,345 B).
- Assets: **528 files / 64.9 MB** — 302 `.mjs`, 119 `.png`, 55 `.woff2`, 21 `.svg`,
  11 `.js`, 5 `.webp`, 4 `.mp4`, 3 `.jpg`, 2 `.css`, 1 `.json`.
- Videos (4): `le5CuqDJ1SD31h6Pn4p7ApPTUX4.mp4` (1.73 MB),
  `MLWPbW1dUQawJLhhun3dBwpgJak.mp4` (1.74 MB), `o5LzS8mCCds84jgTpe7xeCi0zM.mp4`
  (9.09 MB), `RQ5SdYB0jpTAYl74f2vYv0tp0Tc.mp4` (8.60 MB).
- Fonts: InterVariable plus fontshare faces (Inter Variable UI / Inter / Inter Display),
  **sans-only**.
- The export ships `.claude/skills/framer-export-to-react/SKILL.md` and
  `scripts/dump-motion-spec.js` — tooling intended to **convert the export to editable
  React + Vite**. Care_Clinic is not React and does not use this pipeline; the skill is
  recorded here only to document provenance.

---

## 1. Page & section structure [verified]

### 1.1 Home (`/`)

In order: hero (headline + 4.9/5 rating badge), About + stat counters, 5 service cards,
"Why choose us" (4 items), Departments grid, appointment-form band, health packages
(3 price cards), testimonial carousel, doctors grid, FAQ accordion (6 items), blog/news,
closing CTA ("Make an appointment today…"), footer.

### 1.2 About (`/about`)

Hero, mission/vision, stat counters (**Years of Excellence / Expert Doctors / Patients
Treated / Patient Satisfaction**), "How it works" **4 numbered steps (01–04)**, a
gallery marquee/ticker, doctors grid.

### 1.3 Pricing (`/pricing`)

Hero, 3 plans (**Basic / Standard / Premium**), a feature comparison table.

### 1.4 Recurring structural devices [verified]

- **Eyebrow / kicker label** above most section headings (sentence-case or caps).
- **Section header block = label + heading + supporting paragraph.**
- **Numbered step list** with large index numerals (01–04).
- **Stat counters** (animated integers).
- Alternating tinted / plain bands; a **"Glass Effect"** element (3 uses, glassmorphism).
- Responsive triples: duplicated `data-framer-name` values of `Desktop` / `Tablet` /
  `Phone` explain repeated headings in the raw HTML (they are breakpoint variants, not
  duplicated content).
- Frequent `data-framer-name` tokens: `Icon` (×81), `Line` (×47), `Departments` (×40),
  `Book an appoinment` (×22), `Smooth Scroll`, `Glass Effect`.

---

## 2. Layout & visual-language patterns [verified → inference]

### 2.1 What Hospic does structurally [verified]

- Generous vertical rhythm between large, self-contained **bands**.
- A **shared section-header block** reused across every band (label / heading / lede).
- A **card grid** idiom (services, departments, doctors, pricing) with rounded corners
  and soft elevation.
- **Numbered sequences** for process content.
- **Statistics rendered as large tabular numbers.**
- A **closing CTA band** and a **multi-column footer**.

### 2.2 What is transferable as *grammar* [inference]

These are layout *ideas*, not assets, and all are already consistent with Care_Clinic's
approved direction (`docs/frontend-design-exploration.md`, Concept A "Editorial
Clinical" + Concept C "Modern Medical Journal"):

1. **A single reusable section-header block.** Hospic proves the value of one header
   grammar repeated everywhere; Care_Clinic already has `.band__head` + `.eyebrow` +
   `.section-title` + `.section-intro`. Keep and tighten it.
2. **A short rule above the section label** as the structural lead-in (the exploration
   proposed a `40px × 2px` teal rule; Hospic's use of hairline rules validates the
   pattern).
3. **A "figure plate" with a caption** — the journal idiom (Concept C): a bounded
   aspect-ratio block that carries a visual motif plus an honest caption, rather than a
   full-bleed decorative wash.
4. **Large tabular numerals for real counts** — already present as `.trust-strip` /
   `.trust-value`; arithmetic numbers stay in the sans/mono stacks.
5. **A genuine ordered sequence** for "how it works" — already present as the
   `.about-steps` ordered list.
6. **Bands separated by rules + spacing**, not by alternating shadow washes.

### 2.3 What is a *tell* / off-direction (do not adopt) [inference]

- Hero rating badge (4.9/5) and package pricing → **unverifiable claims / no data**
  (prohibited by the spec §E and §J).
- Glassmorphism, gradient washes, drop-shadowed card grids → off the editorial
  direction and flagged by the design skills.
- Web fonts (Inter/fontshare) → ADR-020 forbids web fonts.

---

## 3. Typography [verified]

- Hospic is **sans-only** (Inter family + fontshare display faces).
- Care_Clinic is deliberately **serif-display + sans-UI** (ADR-020, Phase 1 typography).
  This is a divergence we keep — the serif is the differentiator that stops the site
  reading as a generic SaaS template.
- **No Hospic font file, family or metric is reused.** Numerals/times remain in the
  sans/mono stacks (Phase 1 decision).

---

## 4. Motion [partly verified / mostly not verified]

### 4.1 Statically observable [verified]

- Serialized Framer animation hooks: `__framer__enter` (52), `__framer__exit` (52),
  `__framer__animate` (50), `__framer__animateOnce` (50), `__framer__threshold` (50),
  `__framer__loop*` (3 loop effects), `__framer__presenceInitial/Animate` (2).
- Easing family present in the markup: `cubic-bezier(0.44, 0, 0.56, 1)`.
- A **Smooth Scroll** (`data-framer-name="Smooth Scroll"`) → Lenis-style inertial scroll.

### 4.2 Documented from a prior live probe [verified as documentation]

`docs/animation-reference-analysis.md` (produced earlier from the live reference)
records: hero visual scale `1.1 → 1` + fade; hero text `translateY(120px → 0)`; one-shot
section reveals; stat counters; sticky service cards; FAQ accordion `250–320 ms`; a
non-sticky header; Lenis smooth scroll.

### 4.3 Not verified here [not verified]

- Exact per-element durations, stagger intervals and spring parameters.
- Any scroll-linked / parallax behaviour.
- The `__framer__loop*` infinite effects (3) — content and cadence unconfirmed.

### 4.4 Care_Clinic translation (already decided)

Care_Clinic uses **opacity/transform, one-shot `IntersectionObserver` reveals**, gated by
`prefers-reduced-motion`, with the whole page complete with JavaScript off. This matches
Hospic's *intent* (calm, single entrance, one-shot reveals) without copying its runtime
or adding Lenis/GSAP. **No Lenis, GSAP, Three.js or Framer dependency is added.**

---

## 5. Colour & shape [verified]

- Hospic: teal-forward medical palette, glass/translucency, gradient buttons and
  washes, moderate-to-large corner radii.
- Care_Clinic's palette is already approved and independently derived (ADR-020): teal
  `#0EA5A8`, dark teal `#0B7C80`, soft teal `#E8F8F8`, ink `#1F2937`, muted `#6B7280`,
  line `#E5E7EB`. **Nothing is sampled from Hospic's hex values.** Off-direction
  gradient washes and glassmorphism are **not** adopted.

---

## 6. Licence, content & asset exclusions (non-negotiable)

Hospic is a commercial Framer template. **Do not copy** into Care_Clinic:

1. Any **image** (119 `.png`, 5 `.webp`, 3 `.jpg`) or **video** (4 `.mp4`).
2. Any **font file** (`.woff2`) — also barred by ADR-020.
3. Any **copy / testimonial / statistic** (rating 4.9/5, "Years of Excellence",
   "Patients Treated", package names/prices, blog posts).
4. Any **brand marks** (Hospic name/logo) or the Framer runtime chunks.
5. Any **CSS file** wholesale (the two `.css` files are the Framer bundle).

**Consequence:** Care_Clinic has **no licensed photography**, so any "figure plate" on
the home page must be a **flat, decorative, `aria-hidden` CSS/SVG motif with an honest
caption** — never a fake photograph or invented clinical imagery.

---

## 7. Requirement conflicts surfaced by the reference

1. **Bootstrap 5 vs ADR-020.** The task prompt for the integration stage says "use
   Django templates, Bootstrap 5, CSS, SVG, vanilla JavaScript". The repository's
   binding architecture decision **ADR-020** chooses **hand-built CSS, no framework, no
   CDN, no build step**; the repo contains **zero** Bootstrap references and
   `templates/base.html` links only `css/styles.css` + `js/app.js`.
   **Resolution taken:** follow ADR-020 (hand-built CSS). This is recorded as an open
   conflict for the user to confirm; it is not silently overridden.
2. **Hospic sections with no Care_Clinic data.** Rating badge, packages/pricing,
   testimonials, blog/news, 24/7 or "advanced technology" claims, opening hours,
   address, phone, social links — **all omitted** (spec §E.1). The reference may not
   introduce data the app does not have.

---

## 8. Gap list — items needing a browser to confirm [not verified]

If a future stage needs them, these require running the live reference (out of scope
now): exact hero entrance timings & stagger; the 3 `__framer__loop*` infinite effects;
scroll-linked/parallax behaviour; the FAQ accordion's measured open/close duration in
this build; the pricing comparison-table responsive behaviour; and any hover micro-
interactions on cards/buttons.

---

## 9. Summary — what we take, what we leave

**Take (as grammar only):** one reusable section-header block; a short rule above the
label; a captioned figure plate; large tabular numerals for real counts only; a
genuine ordered list for the process; bands separated by rules + spacing.

**Leave:** all assets, fonts, copy, brand marks and CSS; the rating badge, packages,
testimonials, blog and any invented statistics/claims; glassmorphism and gradient
washes; the Framer/Lenis/GSAP runtime.
