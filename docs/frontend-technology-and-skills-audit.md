# Care_Clinic — Frontend Technology & Skills Audit

> **Type:** Inspection and planning report.
> **Status:** No application code, template, stylesheet, script, model, migration,
> dependency, or setting was changed to produce this document. Nothing was installed,
> committed, or pushed.
> **Date:** 2026-10-17
> **Project:** `C:\Users\Ramprasad\OneDrive\Desktop\Care_Clinic`

This report answers three questions before any redesign work begins:

1. Which agent skills are actually installed, and what do they support?
2. Which specialist skills (Three.js, motion, GSAP/scroll, 3D web, accessible frontend)
   exist in the skills ecosystem but are **not** installed?
3. Given the repository as it actually is, which frontend technology direction should
   Care_Clinic take?

---

## 0. Method & scope of this audit

- **Installed skills** were read directly from `C:\Users\Ramprasad\.agents\skills\`
  (`frontend-design/SKILL.md`, `find-skills/SKILL.md`, `web-design-guidelines/SKILL.md`).
  The built-in `customize-opencode` skill is provided by the runtime, not this folder.
- **Discoverable skills** were found with the skills CLI
  (`npx skills find "<query>"`, the tool the `find-skills` skill drives) against the
  public registry. Results are **catalogue listings only**; none were installed.
- **The repository** was inspected by reading `README.md`, `requirements.txt`,
  `templates/base.html`, `templates/home.html`, `static/js/app.js`,
  `static/css/styles.css` (tokens), the existing planning docs under `docs/`, and
  `git status --short`.
- **No behaviour was executed against the app**; no server was started; no dependency
  was installed.

---

## 1. Installed skills (and what each actually supports)

Five skills are installed locally under `C:\Users\Ramprasad\.agents\skills\`. Of the three
requested, all three are present.

| Skill | Location | Source / scale | What it actually supports |
|---|---|---|---|
| **frontend-design** | `\.agents\skills\frontend-design\SKILL.md` (71 lines) | `anthropics/skills`, ~998K installs on skills.sh | Visual/design direction for **new or heavily reshaped UI**. Full content read — see below. |
| **find-skills** | `\.agents\skills\find-skills\SKILL.md` (141 lines) | local workflow skill | Drives the skills CLI (`npx skills find/add/update`) to **discover and install** skills; verify install count / source reputation before recommending. |
| **web-design-guidelines** | `\.agents\skills\web-design-guidelines\SKILL.md` (39 lines) | vercel | **Review/audit** workflow: fetches the latest Web Interface Guidelines rules at review time and reports `file:line` findings. |
| vercel-react-best-practices | `\.agents\skills\vercel-react-best-practices\` | vercel | React/Next.js performance guidance. **Not directly applicable** — this repo has no React (see §3). |
| vercel-composition-patterns | `\.agents\skills\vercel-composition-patterns\` | vercel | React composition patterns. **Not directly applicable** — no React here. |
| customize-opencode *(built-in)* | runtime-provided | — | Editing opencode's own config/agents/plugins. Not relevant to Care_Clinic's app code. |

### 1.1 `frontend-design` — detailed support

It is a **design-direction** skill, not a code-generation or animation-library skill. What
it actually supports:

- **Grounding the design in the subject matter** rather than a generic template; it asks
  for a concrete subject, audience, and primary job before designing.
- **Aesthetic direction**: deliberate palette, typography, and layout choices specific to
  the brief; a compact token system (4–6 named colours, type roles, a layout concept with
  ASCII wireframes, design principles).
- **Process**: plan → review against the brief → build → self-critique, including
  "spend your boldness in one place" restraint and a written self-critique.
- **A quality floor**: responsive to mobile, visible keyboard focus, reduced-motion
  respected, accessible colour, harmonised palette.
- **Writing/copy guidance**: active voice, specific CTA labels, error/empty-state voice.
- **Anti-default catalogue**: it explicitly flags the phrasings that read as
  AI-generated (cream background + terracotta accent, ALL-CAPS eyebrows, the SaaS-card
  kit, etc.) and pushes for choices made *for this brief*.

It does **not** cover: Three.js/WebGL, GSAP/scroll timelines, performance budgets, or
Django integration. Those need separate expertise or a dedicated skill.

### 1.2 `find-skills` — detailed support

- Search the skills ecosystem (`npx skills find [query]`, optional `--owner`).
- Check the skills.sh leaderboard first; **verify quality** (install count, source
  reputation, GitHub stars) before recommending.
- Present options with name / installs / source / install command.
- Install on request (`npx skills add <owner/repo@skill> -g -y`) — **not performed here**.
- Documented "no results" fallback: help directly or scaffold a new skill with
  `npx skills init`.

### 1.3 `web-design-guidelines` — detailed support

A **review/audit** skill. At review time it fetches
`https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`
and checks files against those rules, reporting terse `file:line` findings grouped per
file. The fetched rule-set (verified this session) covers:

- **Accessibility** (labels, `aria-label`, keyboard handlers, semantic HTML, heading
  order, skip links, `aria-live`).
- **Focus states** (visible `:focus-visible`, never `outline:none` without replacement,
  `:focus-within`, sticky overlays not covering focus).
- **Forms** (autocomplete/name/type/inputmode, clickable labels, inline errors, focus
  first error, placeholder conventions).
- **Animation** (`prefers-reduced-motion`, animate `transform`/`opacity` only, never
  `transition: all`, correct `transform-origin`, interruptible, autoplay controls).
- **Typography, content handling, images** (`width`/`height`, lazy-loading).
- **Performance** (virtualise long lists, no layout reads in render, preconnect/preload).
- **Navigation & state, touch & interaction, safe areas, dark mode, locale/i18n,
  hydration safety, hover states, copy**, and an explicit **anti-pattern** list.

This is directly relevant to Care_Clinic's accessibility goals and to the pre-delivery
audit that `docs/architecture.md` §8 already requires.

**Both `frontend-design` and `web-design-guidelines` are already mandated by the
repository:** `docs/architecture.md:180-181` states the `frontend-design` skill **must**
be loaded and followed when UI implementation begins, and a `web-design-guidelines` audit
will be run before delivery.

---

## 2. Discoverable but **not installed** specialist skills

Found via `npx skills find` (the `find-skills` workflow). **None of these are installed**,
and **nothing was installed during this task.** They are catalogue entries only. Install
counts are as reported by the CLI on 2026-10-17 and are the primary quality signal used by
`find-skills`.

> **Key distinction — skills vs runtime dependencies.** An *agent skill* is
> knowledge/workflow the assistant loads; it does not ship to the user's browser and does
> not create a build step or a runtime dependency. That is why installing a design/animation
> skill does **not** by itself violate `ADR-020` (which governs the *frontend runtime*, not
> the agent's tooling). Adopting the *libraries* those skills teach is a separate decision
> (see §4).

### 2.1 Three.js / WebGL

| Skill | Installs | Notes |
|---|---|---|
| `cloudai-x/threejs-skills@threejs-animation` | 18.2K | Largest Three.js set — animation, fundamentals, shaders, geometry, materials, interaction, postprocessing, lighting, loaders, textures |
| `cloudai-x/threejs-skills@threejs-fundamentals` | 15.2K | Same author, core scene/camera/renderer basics |
| `cloudai-x/threejs-skills@threejs-shaders` | 13.6K | GLSL/ShaderMaterial |
| `cloudai-x/threejs-skills@threejs-geometry` / `-materials` | 12.7K each | Geometry & material authoring |
| `cloudai-x/threejs-skills@threejs-interaction` | 12.4K | Raycasting/controls |
| `cloudai-x/threejs-skills@threejs-postprocessing` | 11.8K | Effects/composer |
| `cloudai-x/threejs-skills@threejs-lighting` / `-loaders` / `-textures` | 11.5K / 11.1K / 10.9K | Scene lighting, asset loading, textures |
| `freshtechbro/claudedesignskills@threejs-webgl` | 4.3K | Broader Three.js + WebGL design skill |
| `gamedev-skills/awesome-gamedev-agent-skills@threejs-gltf-loading` | 4.0K | glTF asset loading |
| `nexu-io/open-design@threejs` | 3.3K | Design-oriented Three.js |
| `majidmanzarpour/threejs-game-skills@…` | ~2.7–3.2K | Game-oriented (less relevant to a clinic site) |

### 2.2 Advanced frontend motion design

| Skill | Installs | Notes |
|---|---|---|
| `heygen-com/hyperframes@hyperframes-animation` | 917.4K | Very large install base; general animation |
| `leonxlnx/taste-skill@high-end-visual-design` | 451K | Premium visual/interaction taste |
| `emilkowalski/skills@review-animations` | 231.7K | **Animation review/critique** (Emil Kowalski) |
| `emilkowalski/skills@apple-design` | 217.6K | Motion/interaction craft in an Apple-like idiom |
| `pbakaus/impeccable@animate` | 81.7K | Animation implementation guidance |
| `kylezantos/design-motion-principles@design-motion-principles` | 12K | Motion principles |
| `devmartinese/awwwards-animations-skill@awwwards-animations` | 2.7K | Award-site animation patterns |
| `iart-ai/motion-design-skills@motion-art-direction` / `@animation-principles` | 2.4K / 2.2K | Motion art direction, principles |

### 2.3 GSAP & scroll-triggered animation

| Skill | Installs | Notes |
|---|---|---|
| `greensock/gsap-skills@gsap-core` | 69.4K | **Official GreenSock** — GSAP core |
| `greensock/gsap-skills@gsap-scrolltrigger` | 66.7K | **Official** — ScrollTrigger |
| `greensock/gsap-skills@gsap-plugins` | 62.1K | **Official** — plugin usage |
| `github/awesome-copilot@gsap-framer-scroll-animation` | 3.8K | GSAP/Framer scroll patterns |
| `freshtechbro/claudedesignskills@gsap-scrolltrigger` | 2.7K | Alternative ScrollTrigger skill |
| `freshtechbro/claudedesignskills@scroll-reveal-libraries` | 2.3K | Scroll-reveal library survey |
| `mengto/skills@gsap-scrolltrigger-storytelling` | 1.6K | Scroll-driven storytelling |

### 2.4 High-performance interactive 3D websites

| Skill | Installs | Notes |
|---|---|---|
| `freshtechbro/claudedesignskills@web3d-integration-patterns` | 3.0K | Integrating 3D into a site (currently shows under the GSAP search too) |
| `mengto/skills@build-threejs-scroll-worlds` | 1.3K | Scroll-driven 3D worlds |
| `davila7/claude-code-templates@3d-web-experience` | 1.3K | General 3D web experience |
| `gabremoku/immersive-3d-web@immersive-3d-web` | 56 | Low install count — treat with caution |
| Several `@3d-web-experience` forks | 4–53 | Mostly low-install mirrors; `find-skills` advises caution under 100 installs |

### 2.5 Responsive & accessible frontend engineering

| Skill | Installs | Notes |
|---|---|---|
| `addyosmani/web-quality-skills@accessibility` | 61.7K | Accessibility (Addy Osmani) |
| `addyosmani/agent-skills@frontend-ui-engineering` | 60.1K | Responsive/UI engineering |
| `jakubkrehel/skills@better-accessibility` | 27.2K | Accessibility improvements |
| `ibelick/ui-skills@fixing-accessibility` | 20.4K | Accessibility fixes |
| `wshobson/agents@accessibility-compliance` | 14.3K | Compliance |
| `wshobson/agents@wcag-audit-patterns` | 12.3K | WCAG audit patterns |
| `anthropics/skills@frontend-design` | 997.8K | **Source of the already-installed `frontend-design`** |

### 2.6 Reading of the discovery results

- The ecosystem **does** have high-quality, high-install skills for every requested
  domain. The strongest are the **official GreenSock GSAP skills** and the
  **`cloudai-x/threejs-skills`** set, plus **`emilkowalski/skills@review-animations`**
  and **`addyosmani/web-quality-skills@accessibility`**.
- The installed set is currently **design-audit oriented** (`frontend-design`,
  `web-design-guidelines`) plus two **React** skills that this Django project cannot use.
  There is **no installed** 3D, motion, or GSAP skill.
- **Nothing was installed.** If the project later adopts any of §4, the matching skill
  should be installed first (agent-side only; no runtime impact), per `find-skills`
  verification guidance.

---

## 3. Existing frontend architecture (as found)

### 3.1 Stack — verified

| Layer | Reality in this repo | Evidence |
|---|---|---|
| Backend | **Django 5.2 LTS**, Python 3.12 | `requirements.txt:12`, `README.md` |
| Database | MySQL/InnoDB (SQLite documented local fallback) | `requirements.txt:17`, `README.md` |
| Templating | **Django server-rendered templates** | `templates/`, all app templates |
| Styling | **One hand-built CSS design system**, tokens + components | `static/css/styles.css` — **1,732 lines** |
| Scripting | **Vanilla JS, progressive enhancement only** | `static/js/app.js` — **170 lines** |
| Build pipeline | **None** | no `package.json`, no bundler, no lockfile |
| Framework | **None** (no React/Vue/etc.) | no `package.json`; README explicitly says "No React, Next.js" |
| Frontend deps | **Zero** (no CDN, no fonts, no icon library) | `ADR-020`, `docs/decisions.md:201-221` |
| Images | **None referenced**; brand mark is CSS/SVG | `docs/frontend-design-specification.md` §G |

`package.json` **does not exist** (glob returned no match). There is **no Node build
pipeline**. Do not assume one.

### 3.2 `static/js/app.js` (verified, 170 lines)

An IIFE (`"use strict"`), dependency-free, additive:

- Mobile nav toggle (`aria-expanded`, Escape → close + return focus, close-on-link).
- Filter auto-submit (`[data-autosubmit]`).
- Confirm dialogs (`form[data-confirm]`).
- Double-submit guard (`form[data-guard]`).
- Focus-first-field-error.
- **One-shot `.reveal` via `IntersectionObserver`**, `unobserve()` after first reveal,
  `rootMargin: "0px 0px -10% 0px"`, with an explicit `prefers-reduced-motion` guard that
  reveals everything immediately, plus a 2 s safety net. **This already exists** — the
  reveal pattern the animation analysis recommends is largely implemented.

### 3.3 `static/css/styles.css` (verified tokens)

A mature token system in `:root` (`styles.css:10-131`), including:

- Approved teal palette (`--color-primary: #0ea5a8`, `--color-primary-dark: #0b7c80`,
  `--color-primary-soft: #e8f8f8`), ink scale, semantic colours.
- `clamp()` type scale, spacing scale (`--sp-1…--sp-9`), radii, shadows
  (`--shadow-card`), layout widths.
- **Motion tokens already defined** (`--motion-fast/base/slow/hero/stagger`,
  `--ease-*`, `--reveal-distance: 16px`, `--hover-lift: 3px`).
- A global `prefers-reduced-motion` block, `:focus-visible` rings, pill buttons.

### 3.4 `templates/base.html` (verified)

Shared shell: `no-js`→`js` class swap, skip link, sticky header with role-aware nav
(`user.is_authenticated` / `is_doctor` / `is_staff`), POST logout with CSRF, accessible
flash-message region, multi-column footer, `defer`-loaded `app.js`.

### 3.5 `templates/home.html` (verified)

Already restructured toward the approved direction (Phase 7.3): two-column hero with a
"book by speciality" panel, real-count trust strip, honest About + 3-step list, speciality
grid, doctors grid, closing CTA. Uses `{% url %}` destinations and the `_speciality_card` /
`_doctor_card` / `_empty` partials.

### 3.6 Existing planning docs (highly relevant, part of uncommitted work)

| Doc | Bearing on a redesign |
|---|---|
| `docs/frontend-design-specification.md` | Approved palette, section plan, **content rules (never invent data)**, Django contracts, acceptance checklist |
| `docs/animation-reference-analysis.md` | Verified (browser-measured) motion patterns from the Hospic reference, **motion-token proposal**, reduced-motion + performance requirements |
| `docs/phase-7.4-ui-audit.md` | Application-wide consistency audit (1 high / 5 medium / 6 low), card-system split, proposed fix order |
| `docs/architecture.md` §8 | Frontend direction "Calm clinical clarity"; mandates loading `frontend-design` and a `web-design-guidelines` audit |
| `docs/decisions.md` ADR-020 | **Binding constraint:** hand-built CSS, no framework, no build step, no CDN |

### 3.7 Uncommitted work present (must be preserved)

`git status --short` shows a large in-progress Phase 7.x changeset: **37 modified templates**
plus `static/css/styles.css`, `templates/base.html`, `templates/home.html`, `README.md`,
`docs/{architecture,decisions,implementation-roadmap}.md`; and **new untracked** files:
`docs/animation-reference-analysis.md`, `docs/frontend-design-specification.md`,
`docs/phase-7.4-ui-audit.md`, `static/js/`, `templates/partials/`. Last commit `d474971`.
**No reset/revert/stash was performed.**

---

## 4. Recommended architecture

### 4.1 What the brief asks for, mapped to the repo

Premium healthcare hero (immersive), a **restrained** 3D medical-inspired visual,
sophisticated animation, responsive, accessible, **fast initial load**, Django templates,
existing booking untouched.

### 4.2 Options compared

**A. Three.js directly in Django templates**

Embed a vendored Three.js bundle in a template, render to a `<canvas>` in the hero.

- *Pros:* genuine 3D; the scene can be self-hosted as a static asset (no CDN, no build).
- *Cons:* Three.js core is ~150 KB+ min+gzip before any scene, plus shaders/assets; a
  real GPU cost on mid/low-end Android and on integrated GPUs; the canvas is opaque to
  assistive tech (needs an `aria-hidden` decorative treatment plus a static fallback);
  animation must be manually gated on `prefers-reduced-motion` and on visibility to avoid
  burning battery; it is a **new runtime dependency with a maintenance surface**, which
  the binding `ADR-020` explicitly avoided. Used for a *restrained* motif, the cost/benefit
  is poor for the whole page and questionable even for the hero alone.

**B. CSS-based 3D effects (transforms, perspective, layered SVG/gradients)**

Deepen the existing design system with CSS 3D (`perspective`, `transform-style`,
`translateZ`, tilt-on-pointer) and layered SVG for a parallax "medical" motif.

- *Pros:* **zero dependencies, no build, no CDN** → fully consistent with `ADR-020`;
  trivially decorative (`aria-hidden`), so accessibility is unaffected; the existing
  `prefers-reduced-motion` block and motion tokens already govern it; fastest initial
  load and lowest mobile cost; extends the 1,732-line design system that already exists
  instead of introducing a second rendering model; works with Django templates and leaves
  the booking flow untouched.
- *Cons:* pseudo-3D only — no real meshes/lighting. For a calm clinical brand this is
  generally a feature, not a limitation.

**C. Separate React-based frontend**

A Vite + React + `@react-three/fiber`/GSAP SPA consuming a DRF API.

- *Pros:* the richest 3D/animation ecosystem.
- *Cons:* introduces a **Node build pipeline** (undoes `ADR-020`), a second deployment
  target, an API layer that does not exist, and a **rewrite of every server-rendered
  template including the booking flow** — directly conflicting with the "leave existing
  booking functionality" requirement and the 205-test contract in
  `frontend-design-specification.md` §K. Largest initial JS payload and the slowest first
  load. **Not justified** for a mostly content-and-forms clinic app.

### 4.3 Comparison matrix

| Criterion | A. Three.js in Django | **B. CSS/SVG 3D (recommended)** | C. React SPA |
|---|---|---|---|
| Performance / initial load | Heavy JS, GPU cost | **Lightest** | Heaviest |
| Maintainability | New 3D codebase + asset pipeline | **Extends existing design system** | New app + API + build |
| Deployment complexity | Low (static bundle) | **None added** | High (build + two hosts) |
| Mobile devices | Battery/thermal risk | **Cheap; CSS compositor only** | Highest cost |
| `prefers-reduced-motion` | Manual, easy to get wrong | **Already global; near-free** | Requires per-component handling |
| Accessibility | Canvas opaque to AT; needs fallback | **Decorative by construction** | Re-implement from scratch |
| Adherence to `ADR-020` | Conflicts (new heavy dep) | **Compliant** | Violates |
| Preserves Django booking | Yes | **Yes** | No (rewrite) |
| Matches "restrained" brief | Overkill risk | **Fits** | Overkill |

### 4.4 Recommendation

**Primary: Option B — CSS/SVG-based pseudo-3D on the existing Django + design-system
stack.** It is the only option that simultaneously satisfies "immersive hero", "restrained
3D medical-inspired visual", "sophisticated animations", responsive/accessible, **fast
initial load**, Django templates, and untouched booking — and it is the only one that
respects the binding `ADR-020`.

**Optional, bounded: a thin sliver of Option A, as progressive enhancement only.**
If a genuinely spatial hero element is wanted later, allow **one** self-hosted,
lazy-loaded canvas confined to the hero, with a hard rule set:

- Vendored locally under `static/` (no CDN, no build) — or a smaller library (`ogl`,
  raw WebGL) instead of full Three.js.
- Rendered into `<canvas aria-hidden="true">`; a CSS/SVG fallback is the default and is
  replaced only when WebGL is available **and** `prefers-reduced-motion` is not set
  **and** the device is not low-power.
- Loaded **after** first paint; paused on tab-hidden; **reduced-motion and reduced-data
  disable it entirely**.
- Treated as purely decorative — it must never carry content or control.

This keeps the 3D as an accent, not a dependency, and preserves every guarantee above.

**Do not choose Option C.**

---

## 5. Proposed design direction

Build on the approved "calm clinical clarity" teal identity already in
`frontend-design-specification.md` and the measured motion language in
`animation-reference-analysis.md`; do not invent a new brand.

- **Palette & type:** keep the mandated teal tokens and the system font stack
  (`styles.css:10-131`). No web fonts (no-build/no-CDN).
- **Immersive hero (CSS/SVG):** layered soft-teal gradient mesh + abstract line-art
  "vitals/pulse" motif (concentric rings, ECG trace, cross) drawn as inline SVG, given
  depth with parallax layers and a subtle pointer-driven tilt (`perspective` +
  `translateZ`). One orchestrated entrance — a short staggered fade/translate of
  badge → headline → lead → actions (16 px, per the existing `--reveal-distance`), **no
  hero zoom**, no looping/ambient motion.
- **Restrained "3D":** depth from CSS `perspective` on the hero panel and card `:hover`
  lift (already `--hover-lift: 3px`), plus a decorative floating SVG motif. Not meshes.
- **Sophisticated animation:** reuse the existing motion tokens and the current
  one-shot `.reveal` `IntersectionObserver` in `app.js`; add hover⇄`:focus-visible`
  parity for card lifts and any CTA child reveal. Animate **only `opacity`/`transform`**.
- **Accessibility & reduced motion:** decorative visuals `aria-hidden`; the global
  reduced-motion block must force every animated element to its final state; no content
  ever depends on motion or on JS.
- **Content honesty (non-negotiable):** obey `frontend-design-specification.md` §J —
  no invented ratings, credentials, hours, prices, testimonials, or 3D "trust" imagery.

---

## 6. Risks and constraints

| # | Risk / constraint | Impact | Mitigation |
|---|---|---|---|
| 1 | **ADR-020 is binding** — no framework, no build step, no CDN, no web fonts | Rules out C and a naive A | Recommended B; any A strictly as a self-hosted, lazy, optional accent |
| 2 | **205-test behavioural contract** (`spec` §K) — URL names, context vars, form field names, CSRF, test-asserted strings | A visual change that renames or restructures can fail tests | Presentation-only; never touch routes/forms/views; run the suite after every change |
| 3 | **Large uncommitted Phase 7.x changeset** | Losing work | Preserve everything; no reset/revert/stash; commit only when asked |
| 4 | **Performance budget on mobile** → "fast initial load" | Heavy JS/3D defeats the brief | Keep JS small; CSS/transform-only; any 3D lazy + gated |
| 5 | **`prefers-reduced-motion` / no-JS correctness** | Motion users stranded on hidden content | Global reduced-motion block + default-visible content; JS only enhances |
| 6 | **No image/font/icon assets exist** | Temptation to fake or hotlink | CSS/SVG illustration; local, licensed assets only if ever approved |
| 7 | **Content fabrication** | Ethical/credibility risk | Strictly obey spec §J; hide unsupported sections |
| 8 | **MySQL/InnoDB validation still pending**; concurrency test skipped on SQLite | Delivery risk unrelated to frontend | Out of scope here; tracked in `docs/mysql-validation.md` |
| 9 | **Frontend already has a card-system split** (Phase 7.4 audit, 1 high) | Redesign could deepen inconsistency | Reconcile cards as part of the work; follow the audit's fix order |
| 10 | **Discoverable 3D/GSAP/motion skills are only useful if their libraries are adopted** | Installing a skill ≠ adding a runtime dep | Install agent skills freely (agent-side); adopt runtime libraries only per §4.4 |
| 11 | **Reduced-data / low-power** devices | Battery, data cost | No gating medium; 3D optional and skippable |

---

## 7. Suggested implementation sequence

Ordered so each step is independently verifiable and low-risk first.

**Phase A — Foundations (no visual redesign yet)**
1. **Load `frontend-design`** (per `architecture.md:180`) and re-read
   `frontend-design-specification.md`, `animation-reference-analysis.md`,
   `phase-7.4-ui-audit.md`.
2. Confirm the token set is the single source of truth; add any missing motion/3D tokens
   to `:root` (no new deps).
3. (Optional, agent-side) Install the fitting **discoverable** skills —
   `greensock/gsap-skills@gsap-scrolltrigger`, `cloudai-x/threejs-skills@threejs-animation`,
   `emilkowalski/skills@review-animations`, `addyosmani/web-quality-skills@accessibility`
   — **only if** their libraries are adopted. Installing skills does not touch `ADR-020`.

**Phase B — Consistency first (from the 7.4 audit, lowest risk → highest)**
4. Resolve dead CSS / elevation-rule decisions (7.4 §2.7, §2.10).
5. Unify form-control radius and heading wrappers / empty states (7.4 §2.2, §2.5, §2.6).
6. Adopt `_field.html` everywhere; align `novalidate`; replace inline spacing styles
   (7.4 §2.3, §2.4, §2.8).
7. Unify the card system across list/detail pages (7.4 §2.1) — the largest visible change,
   do it with full responsive verification.

**Phase C — Premium hero & motion (CSS/SVG)**
8. Build the layered CSS/SVG hero and the single orchestrated entrance, using existing
   motion tokens; `aria-hidden` the decoration.
9. Add hover⇄`:focus-visible` parity; confirm transform/opacity-only animation.

**Phase D — Optional, bounded 3D accent (only if justified)**
10. Prototype one lazy, self-hosted, gated canvas (or a lighter WebGL library) behind a
    feature check; keep the CSS/SVG fallback as the default. Measure, then decide.

**Phase E — Verification & audit**
11. Test at **390 / 768 / 1024 / 1440 px**; keyboard, screen reader, and no-JS passes.
12. Toggle `prefers-reduced-motion` (and reduced-data) → all content visible, no motion.
13. Run `python manage.py check`, `makemigrations --check --dry-run`, and the **full test
    suite** (no failures, no new migrations, no new skips).
14. Run a **`web-design-guidelines` audit** before delivery (per `architecture.md:181`).
15. Reconcile `README.md` §11 with the final direction in a documentation pass.

---

## 8. Summary

- **Installed:** `frontend-design` ✅, `find-skills` ✅, `web-design-guidelines` ✅
  (plus `vercel-react-best-practices` and `vercel-composition-patterns`, which do not
  apply to this non-React project). The first two design skills are already **mandated**
  by the repository's own architecture doc.
- **Discoverable but not installed:** strong, well-adopted skills exist for Three.js/WebGL,
  motion design, GSAP/ScrollTrigger, interactive 3D sites, and accessibility — listed in
  §2. **Nothing was installed.**
- **Existing architecture:** server-rendered Django 5.2 + a 1,732-line hand-built token
  CSS system + a 170-line vanilla progressive-enhancement script. **No `package.json`, no
  Node build, no React.**
- **Recommendation:** **Option B — CSS/SVG-based pseudo-3D on the existing Django/design
  system**, with Option A permitted only as a single lazy, self-hosted, reduced-motion-gated
  decorative accent; **not** Option C. This is the only path that satisfies the premium
  brief while respecting `ADR-020`, the test contracts, mobile performance, accessibility,
  and the existing booking flow.

No application code was modified; no dependency was installed; nothing was committed or
pushed.
