# Animation & Motion Reference Analysis — Hospic

**Reference:** <https://hospic.framer.website/> (marketplace: <https://www.framer.com/marketplace/templates/hospic/>)
**Author:** Care_Clinic frontend
**Status:** Analysis only — **no application code was changed** in this task.
**Related docs:** `docs/frontend-design-specification.md` (§H Interaction & motion), `static/css/styles.css`, `static/js/app.js`, `templates/base.html`, `templates/home.html`.

---

## 0. How this was verified (and what was not)

**Live browser inspection WAS performed.** The reference was loaded and driven in a real
Google Chrome (system Chrome `C:\Program Files\Google\Chrome\Application\chrome.exe`, driven
headless via `playwright-core` from a throwaway temp install — **not** added to the project).
Scripts and raw JSON captures live in
`C:\Users\Ramprasad\AppData\Local\Temp\opencode\browserqa\` (`hospic_probe1..11.js`, `*.json`).

**Techniques used**

- Full page load at 1440×900 and 390×844 (mobile UA + touch), waiting for network/animations.
- `document.styleSheets` rule scan for `@keyframes`, `transition`, `animation` (all
  same-origin rules were readable — no CORS gap).
- `document.getAnimations()` (Web Animations API) at rest.
- 16 ms-resolution sampling of `opacity`/`transform`/inline `style` for
  `[data-framer-appear-id]` elements from page start.
- Scroll-into-view sweeps, sampling section children before/after reveal.
- `elementFromPoint`, `:hover` chain, and ancestor/subtree computed-style diffing for hovers.
- Click/tap probes for the FAQ accordion and the mobile hamburger, sampling heights,
  transforms, variant classes and large-fixed-element counts over time.

**Environment caveats that affect confidence**

- Headless Chrome has **no real pointer**, and the site uses **Lenis** smooth scrolling, so
  Playwright's actionability ("element is stable") flaps. Hover probing therefore used raw
  `mouse.move` to coordinates, and some hover targets required retries. Two hover attempts
  missed their target (they hit an overlay / a hidden `ssr-variant` duplicate).
- The DOM contains **hidden responsive duplicates** (`ssr-variant hidden-*`); text locators
  can match a hidden copy. Role-based (`getByRole`) and visibility-filtered lookups were used.
- A Framer **promotional badge** ("Create a free website with Framer…") is injected and
  animates too; it is **not part of the template design** and is excluded below.
- Values below are the **observed** ones. Anything not directly measured is in §2.

**Current Care_Clinic state (already present, for the mapping in §3):**

- `static/css/styles.css`: token-based design system; button/link `transition: … 0.15s`;
  `.service-card:hover` and `.doctor-card:hover` → `translateY(-3px)` + shadow + border
  (0.18s ease); a global `@media (prefers-reduced-motion: reduce)` block that zeroes
  transition/animation durations; `:focus-visible` rings everywhere; **no** `@keyframes`.
- `static/js/app.js` (89 lines): mobile nav toggle (`aria-expanded`, Escape, focus return,
  close-on-link), filter auto-submit, `data-confirm`, submit guard, error-focus. **No
  IntersectionObserver, no counters, no reveal logic.**

---

## 1. Verified Hospic motion patterns

### 1.1 Summary table

| # | Element | Trigger | Motion type | Direction | Duration | Easing | Repeats? | Mobile |
|---|---------|---------|-------------|-----------|----------|--------|----------|--------|
| 1 | Whole page scroll | wheel / drag | Eased smooth scroll (Lenis) | vertical | continuous | eased momentum | continuous | yes (touch, eased) |
| 2 | Hero visual container | page load ("appear") | fade + scale-down | scale `1.1 → 1`, opacity `0 → 1` | ~1.0–1.4 s, starts ~0.4 s after load | strong ease-out / spring-like *(curve est.)* | once | same |
| 3 | Hero text container | page load ("appear") | fade + slide-up | `translateY(120px → 0)`, opacity `0 → 1` | ~1.0–1.2 s, starts ~0.1 s after #2 | strong ease-out / spring-like *(est.)* | once | same |
| 4 | Section containers (Services, form, FAQ, …) | scroll into view | fade + slide-up, **one-shot** | `translateY(120px → 0)`, opacity `0 → 1` | ~1.0–1.2 s | ease-out *(est.)* | **no** (does not replay) | same |
| 5 | Stat counters (About) | scroll into view | count-up (0 → target), digit-by-digit | n/a (numeric) | ~2–3.5 s to settle | linear-ish *(est.)* | once | same |
| 6 | Service cards | scroll | **sticky stack/pin** | each card pins, next covers it | scroll-linked | n/a | scroll-linked | stacks |
| 7 | FAQ item | click / keyboard | accordion expand | height grows (answer revealed) | ~250–320 ms | ease-out *(est.)* | per toggle | same |
| 8 | CTA button child (arrow/overlay) | hover | scale + slide-in of a child node | `scaleX 0.48 → 1`, `translateX 44.7px → 0` | ~600 ms | ease-out with slight overshoot *(spring-like)* | per hover | n/a (touch: tap) |
| 9 | Header / top nav | scroll | **none — not sticky** | scrolls away with page | — | — | — | same |
| 10 | Mobile hamburger | tap | reveal large menu panel | panel appears (slide/fade detail unmeasured) | ≲ 200 ms (appeared between samples) | unmeasured | per open | mobile only |

### 1.2 Effect-by-effect detail (with measurements)

**1. Smooth scrolling — VERIFIED.** The document root carries `HTML.lenis lenis-autoToggle`,
i.e. the site uses the **Lenis** smooth-scroll library. Every scroll-linked effect inherits
its eased/momentum feel. Care_Clinic does **not** need Lenis (see §3/§7).

**2–4. Motion mechanism — VERIFIED.** There are essentially **no CSS animations**:
`@keyframes` count = **0**; only **6** `transition` rules exist in the whole stylesheet and
they target editor chrome and a couple of text-colour links (e.g.
`color 0.7s cubic-bezier(0.44,0,0.56,1)`), **not** the hero/cards. All the motion is applied
by Framer's JS runtime as **inline `transform`/`opacity`** with `will-change: transform`.
`document.getAnimations()` was **empty after load**, and **0** transforms changed over 1.5 s
of idle sampling → **no looping/ambient animation**. This matters: the reference achieves its
motion with JS + inline styles, which is exactly why Care_Clinic should reproduce it with
**CSS transitions/keyframes + IntersectionObserver** instead of copying the Framer approach.

**2. Hero visual entrance — VERIFIED (trajectory captured).** Element `.framer-zwez85`
(hero visual container):
`opacity 0.001, transform scale(1.1)` → animates → `opacity 1, transform none`.
Sampled keyframes (ms since load → value): 416 → o 0.034 / s1.097; 561 → o 0.505 / s1.049;
691 → o 0.748 / s1.025; 1031 → o 0.957 / s1.004; ~1259 → transform `none`. So it is a
**fade + zoom-out from 1.1 to 1**, finishing in roughly **1.0–1.4 s**, beginning ~0.4 s after
DOM content.

**3. Hero text entrance — VERIFIED.** Element `.framer-gc7qf9` (hero copy block):
`opacity 0.001, translateY(120px)` → → `opacity 1, translateY(0)`. Keyframes: 512 → o 0.002
/ y119.8; 626 → o 0.375 / y75.0; 801 → o 0.762 / y28.6; 1131 → o 0.955 / y5.4; ~1740 →
`none`. It **starts ~100 ms after the visual** (a deliberate stagger) and uses the same
**fade-up-from-120px** language. The opacity curve reaches ~0.76 at ~24 % of its window and
then approaches 1 very slowly → an **ease-out with a long settle** (spring-like). Exact
curve not measured (§2).

**4. Scroll-triggered section reveals — VERIFIED, one-shot.** Section-level containers begin at
`opacity 0, translateY(120px)` and animate to `opacity 1, translateY(0)` when they enter the
viewport. Confirmed mid-reveal on **Services** (`.framer-r5ruds`), the **appointment form**
(`.framer-ug8c5f`), an unnamed band (`.framer-nb7tmz`) and the **FAQ** (`.framer-94tejf`),
each settling toward `opacity ~0.97, translateY ~4px` at the sampling instant. Crucially,
sections that had already been revealed earlier in the session stayed at `opacity 1` — the
reveal **does not replay** when re-entering the viewport.

**5. Stat counters — VERIFIED.** The About band contains digit tokens that read `0 0 0 +`,
`0 0 %`, `0 0 / 0` before reveal and count up when scrolled into view. Observed:
`0 1 0 0 +` (mid) → **200+ "Experienced Doctors"**; `3 4 1 2 %` → **98 % "Patient
Satisfaction"**; `0 1 0 1 / 0 1` → **24/7 "Emergency Care"**, settling within ~2–3.5 s.
They animate **only real target values** and carry their unit suffix.

**6. Sticky service cards — VERIFIED.** The four service card containers are
`position: sticky` (`.framer-bfkvc2`, `framer-1btysad`, `framer-yv71gu`, `framer-1xcszjd`,
`framer-rd2nzz`). As you scroll the "Our Services" section, each card **pins and is covered
by the next** — a stacked-card scroll effect. It is scroll-linked (no timed animation).

**7. FAQ accordion — VERIFIED.** FAQ items are Framer *variants*: the first item is
`data-framer-name="Open"` (class `framer-v-xzejsz`, `tabindex="0"`, `data-highlight="true"`)
and the rest are `"Close"` (`framer-v-1hgm6cf`). The answer paragraph lives **inside** the
item and is revealed on expand. Clicking a closed item ("Do you accept insurance?"):
`name Close, variant 1hgm6cf, height 74px` → `Open, variant xzejsz`, height
`86 → 104 → 121 → 127 px` across 80 ms samples → settles at **127 px** in ~**250–320 ms**,
i.e. an **eased height expansion** revealing the answer. One item open at a time, first open
by default. (Native `<details>` is **not** used — `detailsCount = 0`.)

**8. CTA button hover — VERIFIED (child transform).** Hovering the "Find doctors" CTA left the
button's own background unchanged (`rgb(16,106,217)` throughout) but a **child element**
animated in: `transform` went
`matrix(0.48,0,0,1,44.7,0)` → `(0.81,…16.8)` → `(0.95,…4.3)` → `(0.99,…0.7)` →
`(1.00014,…,-0.01)` → `(1.00104,…,-0.09)`. That is a **scaleX 0.48 → 1** combined with
**translateX 44.7 px → 0**, i.e. an icon/overlay that **slides + scales in on hover**, taking
~**600 ms** with a tiny **overshoot** (spring-like). Note the *button background does not
change* — the motion is a child reveal.

**9. Header — VERIFIED not sticky.** The top navigation is wrapped in an
`position: absolute` container at `top:0; z-index:10`; it is **not** fixed/sticky. Sampling
`elementFromPoint(720,30)` after scrolling showed page/hero content, not a floating bar — the
header **scrolls away** and is not re-shown.

**10. Mobile navigation — VERIFIED it opens (detail partial).** On a 390-wide mobile viewport
the hamburger is **three 2 px "Burger Lines"** divs (plus `Burger Lines Transform` wrappers)
at the top-right. Tapping it made a large hidden panel appear —
`framer-15ivizx-container`, `height ≈ 451px`, `position: absolute` — the count of large
fixed/absolute elements went **17 → 18** within ~90–180 ms. The panel's transform was already
at `translateX(-195px)` on first capture, so the **exact reveal animation (slide vs fade,
duration) was not resolved** (see §2). What is verified: **tapping the hamburger opens a large
menu panel.**

**Global characteristics (verified):**

- **No `@keyframes`, no ambient/looping animation**, `getAnimations()` empty at rest.
- Motion is **`transform`/`opacity` only** (no animated width/left/top observed on the moving
  layers), with `will-change: transform` on animated nodes.
- **No CSS-only hover** on nav links / cards was captured changing transform/bg/shadow; the
  one clear hover motion was the CTA child reveal (#8).
- No console errors during any probe.

---

## 2. Unverified assumptions (estimates — do **not** present as measured)

Marked `[ESTIMATE]` throughout. These are reasoned from sampled points, not frame-exact:

- `[ESTIMATE]` **Exact easing curves / spring params.** The entrance and reveal curves behave
  like a strong **ease-out with a long settle** (spring-like) and the CTA hover shows
  **slight overshoot**, but the precise `cubic-bezier`/spring values were **not** extracted.
- `[ESTIMATE]` **Exact durations & delays.** Timing comes from ~16 ms polling with
  network/render jitter; treat "~1.0–1.4 s", "~600 ms", "~250–320 ms" as approximate.
- `[ESTIMATE]` **Hero scale transform-origin** (centre vs edge) was not measured.
- `[ESTIMATE]` **Per-item stagger within a revealed section** (cards/rows appearing in
  sequence) was not isolated; only the whole-container reveal was captured.
- `[ESTIMATE]` **Mobile menu reveal animation** (slide direction, fade, duration) — the panel
  appeared but its trajectory was not captured.
- `[ESTIMATE]` **Nav-link hover** — no colour/transform change was captured; a subtle
  underline/opacity variant *may* exist but is unconfirmed.
- `[ESTIMATE]` **Service/doctor card hover** — no transform/background/shadow change was
  captured on the sampled nodes; a very subtle effect may exist but is unconfirmed.
- `[ESTIMATE]` **Counter duration/curve** — final values were reached between the first and
  ~3.5 s sample; the exact count duration and easing are unknown.
- `[ASSUMPTION]` **Scroll-reveal trigger threshold** (how far into the viewport the reveal
  fires) was not measured.
- **Not attempted:** keyboard-driven focus motion, motion under `prefers-reduced-motion` on
  the reference, and reduced-data/low-power behaviour.

---

## 3. Recommended Care_Clinic equivalents

Principle: **keep Care_Clinic calm and functional.** Reproduce the *language* (restrained
fade/slide reveals, one-shot, real-value counters, honest hover feedback), **not** the exact
magnitudes. Hospic's reveals travel **120 px** and its hero scales from **1.1** — too much for
a clinical booking tool. Recommend **12–24 px** reveals and **no** hero zoom (or a very slight
`1.02`), and **no** Lenis dependency.

| # | Hospic (verified) | Care_Clinic equivalent | Where |
|---|-------------------|------------------------|-------|
| 1 | Lenis smooth scroll | **Do nothing / native scroll.** Optionally `scroll-behavior:smooth` only for in-page anchors, disabled under reduced-motion. | CSS |
| 2 | Hero visual `scale 1.1→1` + fade | Hero already full-bleed teal; use a **subtle** `opacity 0→1` (optional tiny `scale 1.02→1`) on `.hero__panel`/hero art. | `home.html`, `styles.css` |
| 3 | Hero text fade + `translateY(120→0)` | `.hero__copy` fade + `translateY(16px → 0)`, staggered (badge → h1 → lead → actions) by ~60–80 ms. | `home.html`, `styles.css` |
| 4 | Section reveal `120px→0`, one-shot | `.reveal` utility class + **IntersectionObserver** adding `is-visible`; CSS transition `opacity`/`translateY(16px→0)`; **unobserve after first reveal** (no replay) matching the reference. | `styles.css`, `app.js` |
| 5 | Count-up counters (real values) | Keep the existing trust strip **static** by default; *if* animated, count only `speciality_count`/`doctor_count` (already real), ≤1.5 s, and **render the final number immediately** under reduced-motion / no-JS / failure. | `home.html`, `app.js` |
| 6 | Sticky stacked service cards | **Optional, low priority.** If added, use `position: sticky` on `.service-card` inside a defined scroll range **with a no-JS fallback that is a normal grid** (current design). Only if it does not hurt scanning/dashboards. | `styles.css` |
| 7 | FAQ accordion (~250–320 ms height) | Prefer **native `<details>/<summary>`** (zero-JS, accessible, keyboard-native) with a CSS `grid-template-rows: 0fr → 1fr` or `max-height` transition (~220 ms). If custom, mirror `_field.html`/`_form_errors.html` semantics and `aria-expanded`/`aria-controls`. *(Note: Care_Clinic has no FAQ today; only add if real content exists.)* | templates + CSS |
| 8 | CTA child slide/scale on hover | Enhance `.btn--primary` with a **child icon/arrow** that translates in on `:hover` **and `:focus-visible`**, ~180 ms, no overshoot (or very slight). Keep the existing 0.15 s background transition. | `styles.css` |
| 9 | Non-sticky header | Care_Clinic header **is** sticky; **keep it sticky** (better for app navigation/booking). Do **not** imitate the reference here. Optionally ease a subtle shadow-in on scroll. | `styles.css` |
| 10 | Mobile panel reveal | Use the **existing** `app.js` nav toggle; add a short (~180 ms) height/opacity transition on `#site-nav.is-open`. Keep no-JS fallback (menu reachable without JS). | `styles.css`, `app.js` |

---

## 4. Motion token proposal

Add a small, single source of truth to `static/css/styles.css` (`:root`), then reference the
tokens everywhere. Values are intentionally **restrained** and use the **approved teal**
palette for any colour aspect.

```css
:root{
  /* durations */
  --motion-fast:    150ms;   /* buttons, chips, focus */
  --motion-base:    220ms;   /* accordion, small reveals */
  --motion-slow:    420ms;   /* section reveals */
  --motion-hero:    560ms;   /* hero entrance (kept short) */
  --motion-stagger:  70ms;   /* per-item delay in a group */

  /* easing */
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);      /* UI feedback */
  --ease-out:      cubic-bezier(0.16, 1, 0.3, 1);    /* entrances/reveals */
  --ease-in-out:   cubic-bezier(0.44, 0, 0.56, 1);   /* symmetric */
  --ease-spring:   cubic-bezier(0.34, 1.56, 0.64, 1);/* tiny overshoot only */

  /* distances (deliberately << Hospic's 120px) */
  --reveal-distance: 16px;
  --hover-lift:      3px;    /* matches existing .service-card/.doctor-card */

  /* colour motion (teal palette) */
  --motion-accent: var(--brand-700); /* #0b7c80 — AA-safe teal for text/UI */
}
```

Usage sketch:

```css
.reveal{
  opacity: 0;
  transform: translateY(var(--reveal-distance));
  transition: opacity var(--motion-slow) var(--ease-out),
              transform var(--motion-slow) var(--ease-out);
  will-change: opacity, transform;
}
.reveal.is-visible{ opacity: 1; transform: none; will-change: auto; }

/* hero stagger */
.hero__copy > *{ opacity: 0; transform: translateY(var(--reveal-distance));
  transition: opacity var(--motion-hero) var(--ease-out),
              transform var(--motion-hero) var(--ease-out); }
.hero.is-ready .hero__copy > *{ opacity: 1; transform: none; }
.hero.is-ready .hero__copy > *:nth-child(1){ transition-delay: 0ms; }
.hero.is-ready .hero__copy > *:nth-child(2){ transition-delay: var(--motion-stagger); }
.hero.is-ready .hero__copy > *:nth-child(3){ transition-delay: calc(var(--motion-stagger) * 2); }
```

---

## 5. Reduced-motion behaviour

`static/css/styles.css` already contains a global block
(`@media (prefers-reduced-motion: reduce) { * { transition-duration:.001ms!important;
animation-duration:.001ms!important; animation-iteration-count:1!important;
scroll-behavior:auto!important } }`). Keep it, and layer the new motion so it is safe:

- **Everything must end in its final state immediately.** Reveals must not leave content at
  `opacity:0` — the reduced-motion rules must force `.reveal { opacity:1; transform:none }`.
- **JS must honour the preference too:** detect `window.matchMedia('(prefers-reduced-motion: reduce)')`,
  and if set, add `is-visible` to all `.reveal` elements immediately and **skip**
  IntersectionObserver/counters (render final values).
- **No smooth scrolling** under reduced-motion (already `scroll-behavior:auto`), and Care_Clinic
  should **not add Lenis at all**.
- **No looping/ambient animation anywhere** (aligns with the reference's own behaviour and the
  existing spec rule "no infinite marquees").
- Prefer **`transition-property: opacity, transform` only** so reduced-motion zeroing never
  breaks layout.

---

## 6. Keyboard & touch interaction requirements

- **Mobile nav (already implemented):** `<button aria-expanded aria-controls>`; toggling keeps
  `aria-expanded` in sync; **Escape** closes and returns focus to the toggle; choosing a link
  closes it on small screens. Any new transition must not delay focusability.
- **FAQ (if added):** prefer **native `<details>/<summary>`** (keyboard + screen-reader for
  free). If a custom widget is built, the trigger must be a real `<button>` with
  `aria-expanded` / `aria-controls`, the answer a labelled region, and it must work with JS off
  (e.g. `<details>` fallback). **Never** make an accordion hover-only.
- **Hover ⇄ focus parity:** every `:hover` effect (card lift, CTA arrow reveal) must have an
  identical `:focus-visible` effect, so keyboard users see the same feedback. Keep the visible
  `:focus-visible` ring (already present) and **never remove outlines**.
- **Touch:** sizes ≥ **44×44 px** for nav toggle, FAQ rows and CTAs; **no hover-only
  information**; tap feedback via `:active` (already have `.btn:active`). Sticky service cards
  must remain fully scrollable by touch and must not trap content.
- **Focus motion:** do not move focus on scroll/reveal; only the existing error-focus and
  Escape-return-focus behaviours should move it.
- **Reduced-motion keyboard users:** reveals resolve instantly, focus never lands on a
  hidden/mid-transition element.

---

## 7. Performance considerations

- **Animate only `transform` and `opacity`.** Never animate `height`, `top`, `left`, `width`
  in a loop. (The reference FAQ animates height; Care_Clinic should use
  `grid-template-rows: 0fr/1fr` or native `<details>` to avoid layout thrash.)
- **IntersectionObserver, not scroll listeners.** One observer, sensible `rootMargin`
  (e.g. `0px 0px -10% 0px`), **`unobserve()` after the first reveal** (matches the reference's
  one-shot behaviour and prevents work).
- **`will-change` sparingly and remove it** after animation (the reference leaves
  `will-change: transform` on many nodes — do **not** copy that; it costs memory).
- **Counters:** drive with `requestAnimationFrame` for **≤1.5 s**, cancel on
  `visibilitychange`/`pagehide`, and skip entirely under reduced-motion or when the value is 0.
- **No new dependencies.** Pure CSS + a **small** IntersectionObserver module in the existing
  `static/js/app.js` (goal: keep total JS well under a few KB). No Lenis/GSAP/Framer runtime.
- **Sticky cards** (if used) cost nothing at runtime but must be tested for repaint cost on
  low-end devices; keep card counts small (homepage already caps at 6).
- **No layout-shifting reveals:** reserve space (reveal changes only opacity/transform), so CLS
  stays low and content is placed before it animates.
- Respect **`prefers-reduced-data`** is optional/out of scope; there is no heavy media to gate.

---

## 8. Implementation checklist

Motion foundations
- [ ] Add the §4 motion tokens to `:root` in `static/css/styles.css`.
- [ ] Add a `.reveal` utility (opacity + `translateY(var(--reveal-distance))` → visible).
- [ ] Extend the reduced-motion block so `.reveal`/hero resolve to their final state instantly.

JavaScript (`static/js/app.js`, small addition, progressive enhancement)
- [ ] Add an IntersectionObserver module that adds `is-visible` and **unobserves** after reveal.
- [ ] Guard with `matchMedia('(prefers-reduced-motion: reduce)')` → reveal immediately, no observer.
- [ ] Ensure **no-JS** renders everything visible (default state is visible; JS adds the
      animation class before/at load, never hides content that JS cannot restore).
- [ ] (Optional) hero stagger via an `is-ready` class added on load.
- [ ] (Only if real counters exist) count up real values ≤1.5 s, render final number as fallback.

Templates
- [ ] Add `.reveal` to homepage section wrappers (trust strip, about, services, doctors, CTA).
- [ ] Keep the existing no-JS-usable mobile nav markup (`aria-expanded`/`aria-controls`).
- [ ] FAQ only if genuine content exists — use native `<details>/<summary>`.

Interaction
- [ ] Give `:hover` effects a matching `:focus-visible` counterpart (cards, CTA arrow).
- [ ] Confirm tap targets ≥44 px; confirm `:active` feedback on buttons.
- [ ] Confirm nothing is conveyed by hover alone.

Verification
- [ ] Toggle `prefers-reduced-motion: reduce` (DevTools emulation) → **no motion**, all content
      visible, no smooth scroll.
- [ ] Disable JS → homepage fully readable; nav usable; no content stuck hidden.
- [ ] Test at 390 / 768 / 1024 / 1440 px; check reveals, sticky behaviour and the mobile menu.
- [ ] `prefers-reduced-motion` off: verify reveals are **one-shot** (no replay on re-scroll).
- [ ] Run `python manage.py check`, `makemigrations --check --dry-run`, and the full test suite —
      **no failures, no new migrations**.
- [ ] Confirm **no** URL names, view context, form field names, CSRF, RBAC, or booking logic
      changed.

---

## 9. Out of scope / must stay unchanged

- Use the **existing Django template architecture**; no JS framework, no animation library, no
  new dependencies.
- **Preserve the approved teal palette** (`#0EA5A8` / `#0B7C80` / `#E8F8F8` etc.) and the AA
  contrast rules (dark teal for interactive surfaces/text).
- **Preserve all booking logic, authentication, RBAC, CSRF, routes and form behaviour.**
- **No application code was edited in this task**, and nothing was committed or pushed.
