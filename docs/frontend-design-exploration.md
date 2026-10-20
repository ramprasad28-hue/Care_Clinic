# Care_Clinic — Frontend Design Exploration

> **Type:** Design exploration (concepts + recommendation). **No application code, CSS,
> JavaScript, template, setting, model, migration, dependency, or test was changed to produce
> this document. Nothing was installed, committed, or pushed.**
> **Date:** 2026-10-17
> **Project:** `C:\Users\Ramprasad\OneDrive\Desktop\Care_Clinic`
> **Direction set by the brief:** *Premium Editorial Healthcare.*
> **Skills applied:** the installed `frontend-design` skill (loaded and followed for this
> exploration); constraints read from `docs/architecture.md` (esp. §8), `docs/decisions.md`
> **ADR-020**, `docs/frontend-design-specification.md`, `docs/animation-reference-analysis.md`,
> `docs/phase-7.4-ui-audit.md`, and `docs/frontend-technology-and-skills-audit.md`.

---

## 0. How to read this document

- **Verified** — observed directly in this repository (file + line) or in the analysis docs.
- **Proposal** — a design decision put forward here for approval; nothing is implemented.
- `[ASSUMPTION]` — a design inference that must be confirmed before implementation.
- Every concept is constrained by three things that are **not** up for redesign:
  1. **ADR-020** — hand-built CSS, no framework, no build step, no CDN, **no web fonts**.
  2. **Server-rendered Django** — no React/SPA; templates + CSS + a tiny progressive-
     enhancement script (no Three.js/GSAP in this phase).
  3. **The contract** — URL names, context variables, form field names, CSRF, RBAC, ownership
     checks, booking transitions, and the test-asserted strings
     (`frontend-design-specification.md` §K) are preserved. This is a *re-skinning + layout*
     exercise, not a behaviour change.
- The approved teal palette is **retained** in every concept (§2.1). Concepts differ in
  *structure, typography, depth and motion*, not in brand colour.

---

## 1. Grounding the design in the subject matter

The `frontend-design` skill requires a concrete subject, audience and job before designing.

- **Subject:** a clinic **appointment management system** — a real, server-rendered product
  where a person browses clinical specialities, finds a doctor who is accepting appointments,
  and picks a real open time; staff then manage those bookings from role-scoped dashboards.
- **Audience, two registers:**
  - *Public visitor* — a prospective patient (or a reviewer evaluating the product) deciding in
    seconds whether this feels credible, calm and easy.
  - *Clinic staff* — a doctor, receptionist or admin working in dense task views all day.
    (Dashboards are intentionally *not* the marketing surface; they stay dense and practical —
    see §7.)
- **Primary job of the public pages:** **earn trust and remove friction to booking.** The most
  characteristic thing in this subject's world is not a stock "smiling doctor" — it is the
  **appointment itself**: a speciality, a named doctor, and an open time on a schedule. Every
  concept below therefore builds its hero and its components around *care pathways and real
  availability*, using only genuine, database-backed values.
- **What we may never fake** (`frontend-design-specification.md` §J): ratings, review counts,
  patient totals, years of experience, credentials beyond the real `Doctor` fields, addresses,
  hours, prices beyond `Doctor.consultation_fee`, "24/7", "award-winning", or testimonials. Where
  a reference-style section needs invented data, it is **omitted**, not faked.

---

## 2. Current state (verified) and a candid critique

The site is already a credible, well-engineered base: a ~1,732-line token CSS system, tokenised
motion, a single vanilla `app.js` (mobile nav, autosubmit, confirm, submit-guard, error-focus,
one-shot `.reveal` via `IntersectionObserver`), an accessible base shell (skip link, landmarks,
`aria-current`, POST logout with CSRF, status carried by text + shape), and — as of Phase 7.4.2 —
**one shared card language** across the homepage and the speciality/doctor listing pages
(`partials/_speciality_card.html`, `partials/_doctor_card.html`).

That said, measured against the `frontend-design` skill's *anti-default catalogue*, the current
homepage leans on several traits the skill explicitly flags as "generated-page" tells:

| Observed (verified) | Skill's flag | Where |
|---|---|---|
| **ALL-CAPS, tracked eyebrow labels** above every section title | "Template chrome that appears whatever the subject: a tracked-out ALL-CAPS eyebrow label above every heading." | `.eyebrow` (`styles.css:1319-1327`), used in every band |
| **A "→" arrow appended to CTA buttons** (circular `.btn__disc`) | "'→' appended to link and button text." | `.btn--arrow` / `.btn__disc` (`styles.css:503-516,1616-1618`) |
| **The SaaS-card kit** — identical rounded cards, one radius, one soft grey shadow, gradient washes | "content chopped into identical rounded cards … the same soft grey shadow under each." | `.service-card` / `.doctor-card` share `--radius` + `--shadow-card`; `.card` was the same |
| **A single default system sans for everything** | "Choose your typefaces deliberately, not the default families you would reach for on any other project." | `--font-display` = `--font-body` (`styles.css:61-64`) |

None of these is *wrong* — but they are **defaults rather than choices**, and the brief now asks
for *premium, art-directed, distinctive* work ("custom visual elements rather than generic
template decoration"). This exploration is therefore less about re-colouring and more about
**choosing a point of view** the current design has not yet committed to.

**Also verified (and to be improved, not thrown away):** the hero is already a deep-teal,
full-bleed, layered radial-gradient composition with an SVG pattern (`styles.css:545-566`) — a
solid, CSS-only "immersive" foundation (the technology audit's recommended **Option B**) that we
can push further without any dependency.

---

## 3. Shared foundations (the compact token system)

Per the skill's process, a short design plan comes first: colour roles, type, layout, principles.

### 3.1 Colour — the retained palette, re-roled

The seven approved colours stay **exactly as specified**. The design opportunity is to give them
*roles* that read as editorial rather than "all-teal SaaS":

| Role | Token (existing) | Value | Editorial use |
|---|---|---|---|
| Page surface | `--paper` | `#FFFFFF` | The **dominant** surface. Editorial calm comes from generous white. |
| Ink (text) | `--color-text` | `#1F2937` | Headlines + body. |
| Muted ink | `--color-text-muted` | `#6B7280` | Meta/captions only (AA-checked per use). |
| Hairline | `--color-border` | `#E5E7EB` | **Structural rules** — the primary "decoration" in an editorial layout. |
| Accent (AA-safe) | `--color-primary-dark` | `#0B7C80` | Buttons, small teal text, active rules. |
| Accent (decorative) | `--color-primary` | `#0EA5A8` | **Large surfaces / graphics only**, never small text on white. |
| Soft surface | `--color-primary-soft` | `#E8F8F8` | Occasional full-bleed tint band; the "cover stock". |

**Rule carried forward:** `#0EA5A8` is never used for small text on white; interactive teal is
`#0B7C80` (white-on-`#0B7C80` ≈ 5.6:1, AA pass). Depth comes from *ink, rules and whitespace*,
not from piling on shadows.

### 3.2 Type — the one place we spend boldness without a font download

ADR-020 forbids web fonts and a build step, but it does **not** forbid *typographic contrast*.
A distinctive editorial voice is achievable with **two distinct system stacks** (no download,
no licence):

- **Display (editorial headlines):** a **system serif** stack —
  `ui-serif, "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, "Times New Roman", "Liberation Serif", serif`
- **UI & body:** the existing **system sans** stack (`styles.css:63-64`).
- **Data / references:** the existing **system mono** for appointment references and slot times
  only (a genuine "record" idiom, not decoration).

The serif-vs-sans split is the deliberate choice that makes the page read *designed for this
brief* rather than generic. Serif body, where used, gets slightly more line-height (skill
guidance). Line length stays **under ~80ch** (serif may go a touch longer).

> `[ASSUMPTION]` A system serif (Georgia/Palatino/Iowan) is acceptable and renders consistently
> across target platforms. This must be validated at 390/768/1024/1440 before adoption; if the
> serif proves too variable, fall back to a **single sans with a committed display weight and
> tighter tracking** (the Concepts still hold).

### 3.3 Layout concept (one line) + principles

> **One sentence:** *a calm, wide-margined editorial page where a serif headline and a single
> dimensional "care pathway" element carry the brand, and everything else is disciplined
> structure built from ink, hairlines and real availability.*

**Principles (the tests every decision must pass):**
1. **Whitespace is the primary ornament.** Reach for space before shadow, gradient or icon.
2. **Structure is information.** Use rules, columns, captions and lists to *encode* hierarchy,
   not to decorate. Numbered markers appear **only** where content is a real sequence (the
   existing 3-step "how it works" list qualifies; specialities/doctors do **not**).
3. **Spend boldness in one place.** Exactly one memorable moment (the hero), everything around
   it quiet (Chanel's "remove one accessory").
4. **Honesty over polish.** Every number, name and time is database-backed.
5. **Motion answers a person or marks one entrance — never an infinite loop.**

### 3.4 Two-pass self-critique (per the skill's process)

*First pass:* a serif-display + hairline-rules + generous-white layout risks sliding into the
skill's *broadsheet/newsprint* default (trait #3: "hairline rules, dense newspaper-like
columns"). *Second pass — what I changed and why:* I deliberately **keep the whitespace airy and
avoid dense multi-column body text**, use the serif only for **display**, keep body in a humane
sans, and allow **one** dimensional element — so the result is *editorial*, not *newspaper*. I
also resist the "cream + terracotta" and "near-black + acid accent" defaults entirely by keeping
the mandated teal-on-white system.

---

## 4. Three distinct homepage concepts

Each concept answers the same eight questions. All three are CSS/SVG-only, preserve the real
"find a doctor" form (a real `GET` to `doctor_list` with the `speciality` param), and invent no
content.

---

### Concept A — *Editorial Clinical*  (typography-led, calm, sophisticated)

> The homepage reads like the opening spread of a well-set clinical publication: a large serif
> headline, deep margins, and the specialities presented as a typographic index — not a wall of
> identical cards.

**Hero composition & hierarchy**
- Full-width, **white or a whisper of `--color-primary-soft`** — no dark slab. A thin teal
  hairline runs along the top of the hero as the only "frame".
- Left column (~60%): a **serif display H1** ("Care that fits your schedule."), a short sans
  lead (≤ 60ch), and two actions. Right column (~40%): the **"Find a doctor" control** styled as
  a quiet editorial form (label + select + inline button), plus a small **typographic index of
  specialities** (real names as text rows linking to each `speciality.get_absolute_url`).
- Eye path: *rule → H1 → lead → (index / form)* — top-to-bottom, left-to-right, unhurried.

```
┌───────────────────────────────────────────────────────────────┐
│ ─────────────────────────────────────────────────────────    ← hairline
│                                                               │
│   Care that fits                       Find a doctor          │
│   your schedule.                       ┌───────────────────┐   │
│                                        │ Speciality    ▾   │   │
│   [sans lead, ~52ch]                   │ [ See doctors ]   │   │
│                                        └───────────────────┘   │
│   ( Book an appointment )  Find a doctor                      │
│                                        Cardiology             │
│   64–120px vertical breathing room      Dermatology           │
│                                        Neurology              │
└───────────────────────────────────────────────────────────────┘
```

**Typography treatment**
- **Serif** H1/H2 (system serif stack, §3.2), single weight, tight-ish tracking; sans for body,
  UI and meta. Headline is large and calm (clamp driving ~56–72px at 1440 — deliberately *not*
  the current 80px slab, which suits a dark hero, not an airy one).
- **Eyebrows removed.** Section lead-ins become a **serif H2** preceded by a **short teal rule**
  (`40px × 2px`), optionally with a small sentence-case caption — a structural device, not an
  ALL-CAPS label.
- Numerals/times in the mono stack where they are *data* (slot times, references).

**Background & visual depth**
- Depth is *typographic*, not dimensional: wide margins, hairline rules, one `--primary-soft`
  band. No drop shadows on cards. A single restrained inline-SVG medical line motif may sit
  faintly behind the index (aria-hidden), drawn at low contrast.

**Doctor / speciality card design**
- **Editorial entries, not SaaS cards.** A **hairline-separated grid/list**: serif entry title,
  a narrow sans description, a bottom-aligned text link with an **animated underline**.
  Speciality = a typographic entry; doctor = a portrait-less entry (serif name, sans meta line
  "Speciality — Qualification", text CTA). Radius reduced; shadow at most a whisper on hover.

**Section transitions**
- Thin full-bleed hairlines between bands + the generous `.band` rhythm already present. Content
  is separated by *rules and space*, not by alternating shadowed card grids.

**Motion & hover behavior**
- **One orchestrated entrance** in the hero: badge/caption → H1 → lead → actions, fade + 16px
  rise, ~70ms stagger (existing `--motion-*` tokens). Sections reveal once (`IntersectionObserver`
  already in `app.js`) with a plain fade.
- Hover/focus: **underline draw** on links; section rule thickens to `--primary-dark`; card
  border strengthens. No lift. Matches `:focus-visible`.

**Mobile adaptation**
- Single column: serif H1 scales down; the speciality index becomes stacked rows; the form keeps
  ≥44px targets. Rules become horizontal separators. Whitespace reduced but kept airy.

**Accessibility & performance**
- Cheapest concept: no shadows/blur/parallax → negligible paint cost; serif is a **system font**
  (zero download, no FOUT). Excellent contrast (dark ink on white). Motion is opacity/transform
  only and fully neutralised under `prefers-reduced-motion`. Risk: **must not tip into
  "plain"** — the single dimensional hero moment from Concept B is what stops that (see §5).

---

### Concept B — *Immersive Depth*  (layered composition, dimensional CSS/SVG, cinematic hero)

> A single cinematic hero: a deep-teal, softly-lit **care-pathway composition** with a floating
> "availability" plate rendered in real CSS 3D — the one memorable moment on the page.

**Hero composition & hierarchy**
- Full-bleed **deep-teal** hero (extending the already-built gradient at `styles.css:552-555`),
  with a **radial gradient mesh** and a faint vitals/ECG line motif.
- Composition is **layered in depth** (`perspective` on the track; children at different
  `translateZ`): back = mesh + rings; mid = H1 + lead + actions (white on teal); front = a
  **floating "today's open times" plate** built from *real* slot/schedule data shape (a stylised
  schedule card), with a **subtle pointer-driven tilt**.
- Eye path: headline first (largest, brightest), then the actions, then the plate as depth cue.

```
┌───────────────────────────────────────────────────────────────┐
│   ◜ mesh ◝              ( aria-hidden decorative layers )      │
│   Care that fits your                    ╭───────────────╮     │
│   schedule.                ← z:0         │ Today          │     │
│                                          │ 09:00  10:30   │  ← z:2 (tilts)
│   [sans lead, white]                     │ 14:00  15:30   │     │
│   ( Book an appointment ) Find a doctor  ╰───────────────╯     │
│   ~~~~~~ ECG line ~~~~~~~~~~~~~~~~~~~~~~~~~~~                 │
└───────────────────────────────────────────────────────────────┘
```

**Typography treatment**
- A **bold sans display** (heavy weight, tight tracking) in white on teal — contrast with A/C's
  serif; a restrained translucent sans lead. This is the concept that owns "cinematic".
- Section headers on light bands may reuse the serif for continuity, or stay sans — flagged as a
  decision if B is chosen standalone.

**Background & visual depth**
- The differentiator: CSS `perspective` + `translateZ`, layered radial gradients, soft inner
  highlights on the plate, and a faint concentric-ring/ECG SVG (aria-hidden). **No
  `backdrop-filter`** (mobile paint cost) — translucency via a solid tint.

**Doctor / speciality card design**
- Dimensional but disciplined: cards get a **subtle tilt within a perspective container** on
  pointer hover and a **two-layer elevation** (resting + hover). Kept to moderate radius. The
  "slot/time" motif ties cards back to the hero plate.

**Section transitions**
- Bands alternate paper / teal-tint with a **soft SVG curve divider** between them for layering;
  sections rise in with a small parallax offset (transform-only).

**Motion & hover behavior**
- Hero entrance ~620ms (`--motion-hero`) with the plate settling; **pointer tilt** (transform)
  and hover depth on cards. **No infinite/ambient motion.** Everything gated:
  `prefers-reduced-motion`, coarse-pointer (`pointer: coarse`) and narrow widths **disable tilt
  and parallax**, leaving a clean static hero.

**Mobile adaptation**
- Touch has no hover → tilt/parallax off; the floating plate flattens into a stacked panel below
  the copy; the mesh simplifies; the motif is reduced or removed to protect paint cost and
  legibility. The dark hero must keep white-on-`#0B7C80` contrast (≈5.6:1).

**Accessibility & performance**
- Decorative layers are `aria-hidden`; the plate, if it shows numbers, uses **real data only**
  (or is purely decorative). Transform/opacity only. **Highest cost of the three** (layered
  gradients + 3D transforms); the heavy treatment is confined to **one hero** and gated by media
  queries, so the rest of the document stays cheap. The tilt must never be the *only* feedback.

---

### Concept C — *Modern Medical Journal*  (structured grid, strong type, photo-ready, restrained)

> The homepage is laid out like the cover + contents of a medical journal: a masthead block, a
> structured metadata rail, a large **figure plate**, and department/contributor entries on a
> strict grid.

**Hero composition & hierarchy**
- A **12-column masthead**. Title block top-left; a **metadata rail** using *real* counts only
  (e.g. active specialities, doctors accepting appointments — `speciality_count` /`doctor_count`,
  sentence-case, never invented); a large **figure plate** with a defined aspect ratio and a
  small caption. Strong serif/sans pairing.

```
┌───────────────────────────────────────────────────────────────┐
│  Care_Clinic                                    Specialities 6 │ ← masthead + rail
│  ─────────────────────────────────────────────  Doctors 4     │
│  Care that fits your schedule.                  Booking · Open  │
│  [serif display]                                               │
│                                        ┌───────────────────┐   │
│  [sans standfirst, ~2 lines]           │  FIGURE PLATE     │   │ ← aspect-ratio box
│                                        │  (CSS/SVG now;    │   │   (photo-ready)
│  ( Book an appointment )               │   photo-ready)    │   │
│                                        └───────────────────┘   │
│                                        Fig. 1 — real availability│
└───────────────────────────────────────────────────────────────┘
```

**Typography treatment**
- High-contrast **serif masthead + sans standfirst**; strict type scale; **captions** in the
  sans/mono small size; column rules. Numerals as data in mono. No eyebrows.

**Background & visual depth**
- **Print-flat.** Depth via grid, rules and the figure plate (thin border + caption). Optionally
  a very faint CSS "paper" texture (repeating linear-gradients), no image.

**Doctor / speciality card design**
- **"Departments"** (specialities): a rule, a serif name, a narrow description, a footer link.
  **"Contributors"** (doctors): a small square avatar (initial-based), name, affiliation
  (speciality), a link. Restrained hover: rule/underline emphasis only.

**Section transitions**
- Minimal; sections separated by rules and a running label. Reveals are simple fades (or none);
  structure carries the page.

**Motion & hover behavior**
- The most restrained of the three: hover = underline + rule emphasis; one fade per section; **no
  lifts, no parallax**.

**Mobile adaptation**
- Grid collapses to one column; masthead stacks; the figure plate becomes a full-bleed band;
  rules become separators. Serif body line-height increased.

**Accessibility & performance**
- Very cheap (flat, no shadows/parallax). Print-like legibility; if serif body is used, more
  line-height. Photo-ready but uses **no photos today** — the plate is a decorative, `aria-hidden`
  visual with **explicit dimensions** so a licensed image can be dropped in later without CLS.
  Risk: can read **cold/institutional**, and "broadsheet" styling is itself a skill-flagged
  default.

---

## 5. Comparison and recommendation

### 5.1 Comparison matrix

| Criterion | **A. Editorial Clinical** | **B. Immersive Depth** | **C. Modern Medical Journal** |
|---|---|---|---|
| Fits "Premium Editorial Healthcare" | **Strong** | Strong (brand moment) | Strong (editorial) |
| Distinguishes from AI-default tells | **High** (drops eyebrows/arrows; serif voice) | Medium (depth is distinctive; gradients can drift generic) | Medium ("broadsheet" is itself a default) |
| Distinctive typography | **High** (serif display vs sans UI) | Medium (sans-only) | **High** (serif masthead) |
| Sophisticated whitespace | **High** | Medium (depth fills space) | High |
| "Layered / pseudo-3D" ask | Low alone | **High** | Low |
| Cinematic hero ask | Low alone | **High** | Medium (masthead) |
| Consistency across public pages | **High** | Medium (hero ≠ app pages) | High |
| Mobile performance | **Best** | Riskiest (gated) | Best |
| Accessibility risk | **Lowest** | Medium (contrast/AT on decorative layers) | Low |
| ADR-020 compliance | Full | Full | Full |
| Risk of feeling "plain"/cold | **Medium** | Low | Medium |
| Implementation surface | Medium | **Large** | Medium |

### 5.2 Recommendation — a **hybrid**: *A as the shell, C as the component grammar, one bounded moment of B*

**Adopt Concept A (Editorial Clinical) as the primary identity**, use **Concept C's structured
grid as the component grammar** for lists and content bands, and take **exactly one** gated
dimensional element from **Concept B** for the hero.

**Why (reasoning):**
1. **A is the truest expression of the brief** ("typography-led, calm, sophisticated") and the
   strongest antidote to the current tells (it *deletes* the ALL-CAPS eyebrows and the appended
   "→", and introduces real typographic contrast) — at the **lowest** performance/accessibility
   risk.
2. **C supplies the scalable grammar the app needs.** Public *listing/detail* pages (and, later,
   dashboards) benefit from C's rule-and-column discipline far more than from A's looser
   editorial rhythm. C's "departments/contributors" entries are the natural evolution of the
   just-unified `_speciality_card` / `_doctor_card` — turning them from SaaS cards into
   editorial entries **without** re-splitting the card system (Phase 7.4's high-severity issue).
3. **One moment of B prevents A from reading "plain".** The brief explicitly asks for *layered
   compositions and tasteful CSS/SVG pseudo-3D* and *restrained cinematic transitions*. We honour
   that with a **single** dimensional hero element — a floating "open times" plate with subtle
   depth and pointer tilt — and nothing else. This is precisely the skill's "spend your boldness
   in one place," and it keeps 3D an *accent*, not a dependency (as the technology audit's Option
   B concluded).
4. **Photography-readiness (C's main unique value) is satisfied without photos.** We build the
   figure plate with a defined aspect-ratio box so a *licensed* image can be dropped in later
   (ADR-013/014/015 deliberately omit doctor photos; the spec §G forbids fake portraits).

**What to avoid from B:** full-page parallax, backdrop blur, ambient looping motion, tilt on
touch, and any 3D that competes with legibility. **What to avoid from C:** dense newspaper
columns and zero-radius everything (a flagged default); keep radius moderate and white space
generous.

**Net direction in one line:** *an airy, serif-headed editorial clinic — structured like a
journal, with one cinematic, gated moment in the hero.*

---

## 6. Reuse / Refine / Redesign inventory

### 6.1 Reuse as-is (foundations — no change needed)
- **Token system** (`:root`, `styles.css:10-131`): palette, spacing, radii, shadows, type scale,
  motion tokens, focus ring. The hybrid *extends* the type tokens (adds a serif display stack); it
  does not replace the system.
- **Motion layer**: `--motion-*` tokens, the one-shot `.reveal` + `IntersectionObserver` in
  `app.js`, and the global `prefers-reduced-motion` block — all already correct.
- **Base shell** (`base.html`): skip link, landmarks, role-aware nav, POST logout + CSRF, message
  region, footer. Layout/visuals change; structure and contracts do not.
- **Form partials**: `_field.html`, `_form_errors.html`; **empty state** `_empty.html`; **status
  badge** `_status_badge.html`; **breadcrumbs**; **stacked responsive tables** (`data-label`).
- **Contracts**: URL names, context vars, form field names, CSRF, RBAC/ownership, booking
  services, and the test-asserted strings (`spec` §K) — untouched.
- **Dashboards** keep their dense components (`.dashboard__head`, `.stat-card`, `.btn--sm`,
  `.table-wrap`); do **not** push the marketing/editorial layout into them.

### 6.2 Refine (evolve in place)
- **Typography** — add the **serif display stack** and a committed display scale/tracking; keep
  sans for UI/body; add the mono role for data. (Highest-leverage change.)
- **Hero** — restructure `.hero` (`styles.css:545-...`) from dark-slab-plus-boxed-form into the
  hybrid editorial hero **with one dimensional plate**; keep the real `GET` form semantics.
- **Cards → editorial entries** — evolve `partials/_speciality_card.html` /
  `_doctor_card.html` from uniform shadowed cards into rule-based editorial entries (serif title,
  narrower description, underline CTA), differentiated by entity. Keep them **shared** (do not
  re-split, per 7.4.2).
- **Section headers** — remove ALL-CAPS `.eyebrow` labels (`styles.css:1319-1327`); replace with a
  short teal rule + serif H2 (+ optional sentence-case caption). Unify `.page-head` /
  `.band__head` / `.section-header` measures (7.4 §2.5).
- **CTA affordance** — reconsider the appended "→" `.btn__disc` (`styles.css:503-516`): keep an
  arrow **only** where direction is meaningful (hero "Book"), otherwise replace with a clearer
  label or an underline-draw link.
- **Elevation rule** — one content-card elevation (7.4 §2.7); lean on rules/whitespace first.
- **Bands & rhythm** — the `.band` spacing is good; refine dividers (hairline or one soft SVG
  curve, not both), and the `.about-visual` SVG motif + `.trust-strip` into editorial components.
- **Header** — keep sticky + transparent-on-home (a deliberate, verified behaviour); refine only
  colour/stroke to the new type system.

### 6.3 Redesign (replace)
- **Concept of a "card"** — the *visual idea* of identical rounded, shadowed, grey-shadowed cards
  is replaced by the editorial-entry grammar (structure, not decoration). *(Note: the legacy
  `.card` CSS was already removed in Phase 7.4.2; the current `.service-card`/`.doctor-card` are
  the ones to evolve.)*
- **Hero panel presentation** — the boxed form panel becomes the editorial control + typographic
  index (semantics preserved).
- **Eyebrow-driven section intros** — removed entirely.
- **Error pages** — `.notice`-based `404/500/403` do **not** exist; design them on the new system
  (deferred to Phase 8 per 7.4 §2.11).
- **"Photography-ready" figure plate** — a **new** component (does not exist today) introduced by
  the hybrid for a future licensed asset; decorative placeholder now.

---

## 7. Cross-cutting requirements (apply to all concepts)

**Accessibility**
- One `h1` per page; logical heading order; landmarks; skip link; `aria-current`; visible
  `:focus-visible` everywhere; hover effects mirrored on focus.
- **No ALL-CAPS decorative labels** and no meaning carried by colour alone (status keeps text +
  shape).
- Serif body (if used) gets increased line-height; line length < ~80ch; contrast verified per
  §2.1 and B.3 rules.
- Decorative SVG/gradients/plates are `aria-hidden`; nothing essential lives in an image.

**Performance (mobile-first, "fast initial load")**
- Animate **only** `transform`/`opacity`; never animate layout properties in a loop.
- **No new dependencies, no web fonts, no CDN** (ADR-020). System serif/sans/mono only.
- Keep the dimensional treatment confined to the hero and gated by
  `prefers-reduced-motion` / `pointer: coarse` / width; avoid `backdrop-filter`.
- Reserve space for media (aspect-ratio boxes) to keep CLS low; reveal changes opacity/transform
  only.
- Keep total JS tiny — the existing `app.js` already covers nav, reveal, guards; the hybrid adds
  at most a small, feature-detected hero-tilt module.

**Motion**
- One orchestrated hero entrance; one-shot section reveals (no replay); hover answers a person.
- **No infinite/ambient animations.** Full `prefers-reduced-motion` parity: all content resolves
  to its final state, no motion.
- Keep the existing tokens; if 3D is adopted, add **bounded** depth tokens (e.g.
  `--tilt-max`, `--perspective`) — proposals only.

**Content honesty**
- Only database-backed values or approved product copy. Unsupported sections degrade to **empty
  states** (already implemented) rather than to invented content.

**Django contracts**
- URL names, context variables, form field names, CSRF, RBAC/ownership, booking services and the
  test-asserted strings (`spec` §K) remain exactly as they are. The redesign is presentation-only.

---

## 8. Out of scope for this phase (and for the concepts)

- No React/Next.js, no SPA conversion; keep server-rendered templates + templates.
- No Three.js or GSAP **yet** (per the brief). Any spatial element is CSS/SVG only.
- No changes to models, migrations, routes, auth, RBAC, forms, booking logic, settings or tests.
- No new fonts, icon libraries, or CDNs; all icons are inline SVG drawn locally.
- No fabricated ratings, reviews, counts, credentials, addresses, hours, prices or testimonials.

---

## 9. Suggested next step (documentation only — do not implement here)

If this direction is approved, the lowest-risk path is:
1. Add the **serif display token + mono role** and re-role the palette (no layout change).
2. Replace the ALL-CAPS eyebrow device with the rule + serif-H2 pattern.
3. Evolve the two **shared card partials** into editorial entries (single card system preserved).
4. Rebuild the **hero** as the hybrid (editorial shell + one gated dimensional plate).
5. Introduce the photo-ready **figure plate** where a large visual is wanted.
6. Verify at 390/768/1024/1440 with keyboard, no-JS, and `prefers-reduced-motion` passes; then
   run `manage.py check`, `makemigrations --check`, and the full suite, and a
   `web-design-guidelines` audit before delivery.

---

*This is an exploration only. The single artefact produced is this document; no application
code, style, script, template, setting, model, migration, dependency or test was modified, and
nothing was installed, committed or pushed.*
