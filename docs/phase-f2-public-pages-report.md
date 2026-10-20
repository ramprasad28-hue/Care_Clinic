# Phase F2 — Public doctor and speciality pages (2026-10-19)

> **Follow-up revision (same day, user-approved): individual doctor portraits.**
> The user approved the F2 design and asked for real individual portraits replacing the initials-only avatars on the three demo doctors, consistently on the listing cards, the profile masthead and the Doctors mega menu. See the **Revision — individual doctor portraits** section at the end of this file.


## Goal

Extend the approved photo-rich editorial design (homepage, hero, footer, mega menus — all preserved) across the three public catalog pages: the doctor listing, the doctor detail profile, and the speciality detail page. Stop after F2; authentication and dashboard redesign are explicitly out of scope.

## Step 1 — Header regression check at 1211px (result: not reproduced)

The reported cropping of the authenticated Log out button at 1211px **was not reproducible with the current Revision-5 header implementation**. Measured and inspected:

- Rect probe at 1211 px and 1210 px for patient / receptionist / doctor / admin scratch pages: account block right edge lands at 1163 px (viewport 1211) — a ~48 px margin inside the container; no element crosses the viewport edge; `.site-nav` remains a single row; the dense band hides staff console links and truncates emails to 10 ch exactly as approved in the navbar report.
- Real screenshot review at 1211 px (`f2_hdr_1211_patient.png`, `f2_hdr_1211_admin.png`): single row, truncated identity ("arjun.meh…" / "admin.wil…"), Book appointment and Log out pills fully visible with margin.
- No navbar change was made (the smallest correct correction is none); the earlier screenshot most likely predates the Revision-5 compaction ladder. Flagged for the reviewer to re-check on their side.

## What was changed

### Speciality detail (`website/templates/website/speciality_detail.html`)

- New **image-led editorial header** (`page-hero`): breadcrumb, hairline rule, uppercase "Speciality" eyebrow, large serif `h1`, the **real** speciality description, a **real count line** ("N doctors accepting appointments", computed from the actual queryset), and two real actions: "Meet the doctors" (anchor to the in-page doctors section) and "All specialities" (existing route).
- The right-hand column shows the speciality's own locally stored, documented photograph (`static/img/specialities/<slug>-card.jpg`, 900×600, `alt=""` — decorative, title carries meaning; rendered only when the file exists via the existing `static_exists` filter, so a missing image degrades to a text-only header rather than a broken one). Honest caption: "Illustrative stock photo".
- Doctors section retained unchanged in behaviour (same context queryset, same `_doctor_card.html` partial, same `doctors-heading` label) but now sits on the homepage's tinted band; the empty state keeps the `+` badge and gains a real "All doctors" action (existing `doctor_list` route) alongside the honest text. Verified live on Cardiology (1 doctor) and Orthopaedics (empty state).

### Doctor listing (`website/templates/website/doctor_list.html`)

- New editorial header using the **documented** `static/img/about/waiting-area.jpg` (1200×960, decorative `alt=""`, reserved 5:4 box, no CLS) with the honest caption "Illustrative stock photo — not the clinic's premises."; copy keeps the original sentences plus a **real** count ("3 doctors accepting appointments").
- Filter form preserved exactly: same `method="get"`, same `speciality` name/id, same `data-autosubmit`, same options and Filter button (verified live: changing the select auto-submits to `?speciality=cardiology` and filters to that doctor).
- Grid section unchanged in data flow; empty state logic preserved exactly (title/text/action/`show_action=selected_speciality`).

### Shared doctor card (`templates/partials/_doctor_card.html`) — listing, speciality detail, homepage

- Stronger hierarchy: name, then the **speciality as an uppercase teal eyebrow label**; meta list now shows qualification (unchanged), the **published consultation fee when present** (`₹600 consultation` — real `consultation_fee` field) and an "Accepting appointments" line with a matching teal status dot (text + dot, never colour alone).
- Real **booking action**: `Book appointment` button per card → existing `appointments:book doctor.slug` route (anonymous users get the existing login redirect with `next`; verified by real mouse click). The profile link remains ("View profile →"), so every previous link still exists; nothing removed.
- Cards are equal-height (flex column, actions pinned) — the ragged alignment in the old grid is gone. The partial is shared with the **homepage** doctors band, which now shows the same refined cards live and coherently (verified by screenshot).

### Doctor detail (`website/templates/website/doctor_detail.html`)

- Polished **profile masthead**: large initials avatar (`avatar--xl` — initials only, per the standing no-stock-portraits rule), "Doctor profile" eyebrow, large serif name, pill cluster (speciality pill links to the speciality page; the real accepting/not-accepting pill), the facts list (qualification, registration number, fee — same fields as before) and a large "Book an appointment" CTA (same conditional, same route). Breadcrumb unchanged.
- Aside keeps the **real weekly availability** mechanics untouched (same queryset/loop/table, same `empty--inline` fallback) and adds one supporting photograph (`img/home/hero-main.jpg`, decorative `alt=""`, reserved box) with the explicitly honest caption: *"Illustrative stock photo — not a photograph of Dr. {name}."* — the image is deliberately separated from the doctor's identity both spatially and verbally. **No `profile_image` field was added; no migrations.**
- The bio renders on its own tinted band (`white-space: pre-line` so multi-paragraph bios keep their line breaks). Fee display unified via `floatformat`.

### CSS (`static/css/styles.css`)

New F2 section (~155 lines, flat design language only): `.eyebrow`, `.page-hero*` (text-first grid, optional media column collapsed at ≤900px), `.band--flush-top`, doctor-card eye/stats/actions additions, `.profile-head*` (2-col masthead → 1-col ≤900px, `avatar--xl`), `.profile-bio*`. All reuse existing tokens (`--brand-*`, `--radius*`, spacing/typography); no gradients, no new fonts, no shadows beyond the existing token set; `prefers-reduced-motion` unaffected.

## Image rules compliance

- Only pre-existing, pre-documented local Pexels assets were reused; **no new images** were obtained, so the manifest needed no additions (waiting-area.jpg and hero-main.jpg were already documented for these exact "atmosphere" purposes; speciality card images are the per-slug files already in the manifest).
- No hotlinking, no Hospic assets, no invented claims anywhere (counts, fees, availability are all model data; captions are honest).
- All hero/plate images are decorative (`alt=""` + the meaning carried by adjacent text; speciality image is `aria-hidden="true"`-equivalent via alt-only; the doctors-panel images were already audited). Responsive sizing via reserved `aspect-ratio` boxes + `width`/`height` attributes (no CLS); `eager` above the fold, `lazy` below.

## Files changed

- `templates/partials/_doctor_card.html` (shared card)
- `website/templates/website/doctor_list.html`
- `website/templates/website/doctor_detail.html`
- `website/templates/website/speciality_detail.html`
- `static/css/styles.css` (F2 section + responsive collapses; no approved design touched)
- `docs/phase-f2-public-pages-report.md` (this file)
- Scratch QA artefacts in temp: `f2keys.mjs` + shots under `shots/` (`f2_*.png`)

No views, models, URLs, migrations, or app.js changes were needed.

## Verification

- `manage.py check` → 0 issues; `makemigrations --check --dry-run` → no changes.
- Full pytest: **227 passed / 1 skipped**; SharedNavigation tests **OK (9/9)**; `git diff --check` clean (only pre-existing CRLF advisories); `git status --porcelain` unchanged at 76 files; nothing staged/committed/destructive.
- Navbar regression on the touched sharing partial: `liveqa.mjs` vs the running server → **37/37, zero console errors** (mega menus, drawer, homepage behaviours all unaffected).
- Route/link audit (real browser, CDP): filter auto-submit ✔ (`?speciality=cardiology`, 1 card, "Cardiology" label), card **Book** click lands on the real booking route (`/appointments/book/aswin-kumar/`) → login redirect with `next` (existing behaviour) ✔, "View profile"/profile cards navigate to real detail pages ✔, speciality hero "Meet the doctors" anchor jumps to `#doctors` ✔, "All specialities"/"All doctors"/breadcrumb links validate ✔.
- Overflow: none at 390/768/1024/1440 across listing, filtered listing, speciality list/detail (populated + empty), doctor detail, homepage.
- Images: every visible image loads (`complete && naturalWidth>0` after scroll); the only "not loaded" images are `loading="lazy"` assets inside the closed nav mega panels, and they are verified loaded when a panel opens (navbar phase test). No broken assets.
- Keyboard: on the doctor page, Tab reaches the primary CTA ("Book an appointment" active after the natural DOM order; breadcrumb and name links in order); anchors and buttons are real links with focus styles.
- Screenshots captured in the required order and **inspected** (all in temp `phase-img/shots/`): doctor listing (`f2_after_doctors_1440.png`, `f2_doctors_{1440,768,390}.png`), doctor detail (`f2_doc-aswin_1440.png`, `f2_doc-rahul_*`, `f2_doc-aswin_{768,390}.png`), speciality detail populated (`f2_spec-cardio_*`) and **empty state** (`f2_spec-ortho_*`), the authenticated header at 1211 px (`f2_hdr_1211_{patient,admin}.png`), and the homepage doctors band (`f2_home_docsband_1440.png`) as the approved-homepage regression check.
- Mid-development fixes made visual, all re-verified: the bio band's double-container offset (`container` + max-width conflict), and the full-page screenshot method (tall viewport) that exposed nothing about the DOM but fixed scratch capture tooling only.

## Remaining limitations

- The empty Orthopaedics/Paediatrics pages are truthful ("No doctors currently available" + "All doctors"); making them feel "less empty" without inventing doctors is not pursued (honesty rule).
- Doctor bios in the DB are one short line each; the bio band's layout is verified with `pre-line` but richer copy is content work, not design work.
- Medicine/fee presentation ("per consultation") mirrors existing page conventions; no new wording claims.
- The 1211 px finding could not be reproduced with the current code (see Step 1); if the reviewer still sees the clipped Log out button, a fresh full-size screenshot of their state would pin the difference (their browser may still hold an older CSS cache — Ctrl+F5).
- Pagination on the doctor list does not exist in the app (single-page ListView without `paginate_by`) — unchanged by design; there is nothing to preserve beyond what's there.

## Revision — individual doctor portraits (2026-10-19, user-approved follow-up)

### Assets (batch 2, documented in `docs/imagery-licensing.md`)

Three distinct licensed Pexels portraits saved locally as `static/img/doctors/<slug>-profile.webp` (CDN-delivered at `w=800` in **webp** format directly — no converter used, no new dependency; RIFF/WEBP magic verified on each file):

| Doctor | File | Source photo | Photographer |
|---|---|---|---|
| Aswin Kumar | `aswin-kumar-profile.webp` (800×1200, 30 KB) | pexels.com/photo/a-portrait-of-a-doctor-5722163 | cottonbro studio |
| Meera Nair | `meera-nair-profile.webp` (800×533, 16 KB) | pexels.com/photo/smiling-doctor-portrait-19963165 | Tessy Agbonome |
| Rahul Verma | `rahul-verma-profile.webp` (800×533, 19 KB) | pexels.com/photo/portrait-of-a-doctor-wearing-a-white-coat-6762869 | Usman Yousaf |

Both selected candidates plus one earlier pick were visually inspected via a real browser screenshot before adoption. Three candidates were **rejected** during selection for honesty/quality reasons (manifest documentation included): a hospital logo ("SUS") visible on clothing (Pexels trademark rule), an off-style dark glamour backdrop, and one photo that was the **same model** as another selected portrait — identical faces for two named doctors would be misleading. All portraits keep: professional clinical clothing, natural expressions, neutral uncluttered backgrounds, `object-fit: cover` crops with `object-position: top`.

**Honesty:** the manifest's standing "initials-only" rule was explicitly superseded by this user instruction for the demo dataset; the manifest now documents these files as **demo portrait placeholders, not verified photographs of real Anmaya Health doctors**, to be replaced one-for-one by genuine consented portraits (same naming convention) when available.

### Slug-mapped wiring (no hard-coded names, no model changes)

- New template tag `doctor_portrait(doctor)` in `website/templatetags/clinic_images.py`: resolves `img/doctors/<slug>-profile.webp` via the existing static-file probe and returns `""` when the file is missing — every caller keeps the initials avatar in that case, never a broken image. The tag reuses the `static_exists` introspection (extracted into a `_file_in_static` helper; behaviour unchanged for `static_exists`).
- Wired into all three individual-doctor surfaces: `_doctor_card.html` (shared by listing card, speciality detail, homepage band), `doctor_detail.html` masthead (`avatar--xl`), and `_nav_doctors_panel.html` (Doctors mega menu items). Portraits are decorative (`alt=""`, `aria-hidden` wrapper); the adjacent name carries the meaning at all sizes.
- Verified: probing listing card, profile masthead and mega menu for all three doctors returns **exactly one unique `src` per doctor** — the same image everywhere.

### CSS (`static/css/styles.css`)

`.avatar--photo` variant: `object-fit: cover`, `object-position: top`, radius bumps (`--radius` cards/menu, `--radius-lg` on the 5.25rem masthead tile), fill of the existing fixed-size avatar boxes (no CLS). No other design tokens changed.

### Interaction fix discovered by the QA suite

`liveqa.mjs` dropped to 36/37: the two lazy images inside the **Doctors mega panel** are in a `display:none` container, so `loading="lazy"` never started fetching them until the panel was open, making the suite's "all menu images loaded" check flaky. Made the three panel portraits (≈65 KB total) and the panel's feature photo `loading="eager"`; the suite returned to **37/37 with zero console errors**. Card/masthead images unchanged (lazy below the fold stays lazy).

### Verification

- `manage.py check` 0 issues; `makemigrations --check --dry-run` no changes; SharedNavigation tests **OK (9/9)**; full pytest **227 passed / 1 skipped**; `git diff --check` clean; `git status --porcelain` = 77 entries (previous 76 + the new untracked `static/img/doctors/` directory with the 3 webp files). Nothing staged/committed; no destructive commands; no model/migration changes (ADR-020 respected — no new dependencies, webp came straight from the CDN).
- Cross-surface identity check: unique `src` per doctor across listing / detail / mega menu (see above).
- Overflow: none at 390/768/1024/1440 for listing, all three detail pages, homepage, speciality detail.
- Mega-menu behaviour unchanged (liveqa 37/37 incl. hover/pin/Escape/drawer blocks).
- Screenshots captured in order and inspected (temp `phase-img/shots/`): portraits source gallery (`f2_portraits_gallery*.png`, used to reject the two unsuitable candidates), **doctor listing with three portraits** (`f2_portraits_listing_1440.png`, `f2_portrait390_doctors.png`), **each doctor detail masthead** (`f2_portraits_detail_{aswin-kumar,meera-nair,rahul-verma}.png`), **Doctors mega menu open with portraits** (`f2_portraits_mega_1440.png`), plus mobile detail (`f2_portrait390_meera.png`). The doctor detail page's separate illustrative consultation photograph remains visually and verbally distinct from the individual portrait (unchanged caption "Illustrative stock photo — not a photograph of Dr. {name}").

### Remaining limitations

- Portrait backgrounds are not pixel-identical across the three photos (navy / charcoal / light-grey studio). Faces, clothing style, crops and sizes are consistent; a full "same studio" look requires clinic-supplied photography, already flagged as the replacement path.
- The initials fallback is verified by code path (tag returns `""` → initials span) rather than with a screenshot, because all three demo doctors currently have portrait files.
- Unsplash hosts the near-identical Usman Yousaf photo set; Pexels was used exclusively (existing manifest convention).
