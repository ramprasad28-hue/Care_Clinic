# Care_Clinic — Imagery Licensing Manifest

> Every raster image in `static/img/` is documented here: **filename · source ·
> licence · acquired · photographer · intended use · alt text**. No image is
> hotlinked; all are stored locally (ADR-020). Generic stock photography is
> used as **atmosphere/illustration only** — nothing here is presented as
> Anmaya Health's actual premises, staff, or doctors (user-approved Revision 3
> rules, plan §6B). This batch (batch 1) is Pexels-sourced; Pexels imagery is
> free for commercial and web use, no attribution required (credited here
> anyway), modification permitted; prohibited uses (direct from Pexels
> license page, verified 2026-10-18): identifiable people may not appear in a
> bad light or offensively; no selling unaltered copies; no implying
> endorsement by people/brands in the imagery; no redistribution as stock; no
> trademark/brand use. Web use on this private project site is an allowed use
> case per that licence.

## Licence summary — Pexels (https://www.pexels.com/license/)

- Free stock photos and videos for commercial use, on websites included.
- Attribution not required (included voluntarily below).
- Modification permitted.
- **Not permitted:** depicting identifiable people in a bad light/offensively;
  selling unaltered copies as physical products; implying endorsement;
  redistributing as stock/wallpaper platforms; use in trademarks.

Acquisitions in this manifest were downloaded from `images.pexels.com`
(resized CDN delivery of the photographer's original), stored re-locally in
the repository. **All images below are illustrative/stock imagery and are
never labelled as photographs of the clinic, its real doctors, or real
patients.**

## Assets (batch 1, acquired 2026-10-18)

| File | Source (Pexels photo) | Photographer | Licence | Source date | Dimensions in repo | Alt text | Intended use |
|---|---|---|---|---|---|---|---|
| `static/img/home/hero-main.jpg` | pexels.com/photo/smiling-doctor-and-patient-shaking-hands-8313187 | RDNE Stock project | Pexels (free, commercial, attribution optional) | 2021-06-12 | 1600×1200 | "A clinician in a white coat warmly welcoming a smiling patient in a light-filled consultation room" | Homepage hero photograph (illustrative; not presented as the clinic's own staff/premises) |
| `static/img/about/waiting-area.jpg` | pexels.com/photo/desk-and-chairs-in-doctor-office-7789614 | Ivan Babydov | Pexels (free, commercial, attribution optional) | 2021-05-06 | 1200×960 | "A calm, tidy clinic consultation room with a wooden desk and two chairs" | Homepage About band figure plate (caption explicitly says "Illustrative stock photo") |
| `static/img/specialities/cardiology-card.jpg` | pexels.com/photo/a-healthcare-worker-measuring-a-patient-s-blood-pressure-using-a-sphygmomanometer-7659573 | Thirdman | Pexels (free, commercial, attribution optional) | 2021-04-27 | 900×600 | empty (decorative; card title carries meaning) | Speciality card tile — Cardiology (atmosphere image, decorative) |
| `static/img/specialities/dermatology-card.jpg` | pexels.com/photo/a-tablet-with-a-magnifier-7446660 | Gustavo Fring | Pexels (free, commercial, attribution optional) | 2021-04-09 | 900×600 | empty (decorative) | Speciality card tile — Dermatology (atmosphere image, decorative) |
| `static/img/specialities/general-medicine-card.jpg` | pexels.com/photo/photo-of-woman-talking-to-the-sick-patient-3985299 | Gustavo Fring | Pexels (free, commercial, attribution optional) | 2020-04-19 | 900×600 | empty (decorative) | Speciality card tile — General Medicine (atmosphere image, decorative) |
| `static/img/specialities/orthopaedics-card.jpg` | pexels.com/photo/physiotherapist-massaging-knee-and-leg-20860603 | Funkcinės Terapijos Centras | Pexels (free, commercial, attribution optional) | 2024-04-01 | 900×600 | empty (decorative) | Speciality card tile — Orthopaedics (atmosphere image, decorative) |
| `static/img/specialities/paediatrics-card.jpg` | pexels.com/photo/a-doctor-checking-a-child-7653108 | Pavel Danilyuk | Pexels (free, commercial, attribution optional) | 2021-04-26 | 900×600 | empty (decorative) | Speciality card tile — Paediatrics (atmosphere image, decorative) |

## Assets (batch 2 — individual demo doctor portraits, acquired 2026-10-19)

| File | Source (Pexels photo) | Photographer | Licence | Source date | Dimensions in repo | Alt text | Intended use |
|---|---|---|---|---|---|---|---|
| `static/img/doctors/aswin-kumar-profile.webp` | pexels.com/photo/a-portrait-of-a-doctor-5722163 | cottonbro studio | Pexels (free, commercial, attribution optional) | 2020-10-28 | 800×1200 (CDN `w=800`, `fm=webp`) | empty (decorative; adjacent name carries meaning) | Demo portrait for the demo doctor **Dr. Aswin Kumar** on the listing cards, profile masthead and Doctors mega menu |
| `static/img/doctors/meera-nair-profile.webp` | pexels.com/photo/smiling-doctor-portrait-19963165 | Tessy Agbonome | Pexels (free, commercial, attribution optional) | 2024-01-22 (repo DL 2026-10-19) | 800×533 (CDN `w=800`, `fm=webp`) | empty (decorative) | Demo portrait for the demo doctor **Dr. Meera Nair** (same three surfaces) |
| `static/img/doctors/rahul-verma-profile.webp` | pexels.com/photo/portrait-of-a-doctor-wearing-a-white-coat-6762869 | Usman Yousaf | Pexels (free, commercial, attribution optional) | 2021-02-09 | 800×533 (CDN `w=800`, `fm=webp`) | empty (decorative) | Demo portrait for the demo doctor **Dr. Rahul Verma** (same three surfaces) |

**Honesty status of this batch (user-approved, supersedes the initial-

portrait-free rule for the demo dataset only):** these three demo doctors
(Aswin Kumar, Meera Nair, Rahul Verma) are seed/demo records, not verified
actual Anmaya Health doctors. The images above are licensed stock used as
**individual demo portrait placeholders** — each is assigned to exactly one
demo doctor via the slug mapping and must never be captioned, alt-texted or
claimed as a genuine photograph of that real-world doctor. Styling is kept
consistent (professional clinical clothing, natural expression, neutral
uncluttered studio backgrounds, portrait crops via `object-fit: cover`,
`object-position: top`). Three candidates were rejected during selection
because they were unusable as individual portraits: one showed a hospital
logo ("SUS") on clothing (trademark-risk per Pexels rules), one had a dark
glamour-style backdrop, and one was the same model as another selected
portrait (identical faces across two named doctors would be misleading).
When genuine, consented portraits for actual clinic doctors exist, they
replace these files one-for-one (same naming convention
`static/img/doctors/<slug>-profile.webp`) and this manifest is updated.

## Rules applied (summary)

- Downloaded and stored locally; no CDN/hotlink in any template (`{% static %}` only).
- ~~Doctor cards keep the honest **initials avatars**~~ **Superseded by
  user-approved batch 2 (above): the three demo doctors now carry individual
  slug-mapped demo portraits, clearly documented as placeholders.** The
  initials avatar remains the graceful fallback for any doctor whose portrait
  file does not yet exist, and nothing is ever presented as a verified
  photograph of a real clinic doctor.
- No claims encoded in imagery (no "24/7", awards, accreditations, patient
  totals). Decorative images are hidden from assistive tech where the image
  adds no meaning (`alt=""`); content images get descriptive alt text.
- Naming convention: `static/img/specialities/<slug>-card.jpg`,
  `static/img/home/*`, `static/img/about/*`,
  `static/img/doctors/<slug>-profile.webp`; `website/templatetags/
  clinic_images.py` renders a tile only when the file exists (graceful
  text-only fallback), so removing a photo never leaves a broken `<img>`.
- Add rows to this manifest for every future image; the batch-1 report is
  `docs/phase-7.5-homepage-imagery-batch-1-report.md`.

## Uploaded imagery — administrator duties (ADR-022, phase C1)

Since C1, the administrator can upload/replace imagery **through Django Admin**
(`Speciality.image`, `Doctor.profile_image`, `website.WebsiteSectionImage`).
These uploads live under `MEDIA_ROOT` (`media/…)`, never overwrite anything in
the source-controlled `static/img/` tree, and the manifest duties extend to
them:

1. **Licensing.** Before uploading, the administrator must hold and record the
   licence for the file (own photo, or a commercial-licensed stock like the
   Pexels assets above). The upload forms validate *decodability/type/size*,
   not licensing — the check is a human duty. Record source, photographer,
   licence, and date in this manifest (add a "batch" table).
2. **Honesty.** No generic stock photo is ever presented as a genuine
   photograph of a real doctor/patient: a `Doctor.profile_image` upload is
   presumed a genuine, consented photograph of that doctor; the
   `doctor_profile_photo_aside` section and any atmosphere upload keeps an
   honest caption ("Illustrative stock photo — …", editable per row).
3. **Replacement chain.** An upload **replaces** the documented static
   fallback for its surface; deactivating or clearing the registry row /
   field reverts the page to the static fallback exactly as before C1. When an
   upload fully replaces a static asset permanently, the static copy may be
   retired and its manifest row updated — statically, never by an upload.
4. **One-way boundary.** Uploads are scoped by `upload_to` callables
   (`specialities/<slug>/card.<ext>`, `doctors/<slug>/profile.<ext>`,
   `sections/<key>/image.<ext>`); they cannot touch the repo's `static/img/`.
5. **Validation (technical).** JPG/PNG/WebP determined by decoded Pillow
   format, ≤ `UPLOAD_IMAGE_MAX_BYTES` (default 2 MiB), SVG/GIF rejected;
   dimension/ratio deviations surface as admin warnings after save.
