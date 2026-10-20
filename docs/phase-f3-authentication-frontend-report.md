# Phase F3 — Authentication frontend redesign (2026-10-19)

## 1. Scope

Frontend-only redesign of the authentication experience (login, registration, the
four-step password reset flow, and the logged-out page) to match the approved
Care_Clinic identity — teal accents, serif display headings, restrained borders,
licensed photography — while **preserving the backend authentication contract
unchanged**. Backend auth logic (views, forms, URLs, validators, redirects) was
inspected and left untouched; email templates are plain text and were not
modified.

Backend files inspected (Step 1, no changes): `accounts/forms.py`
(`EmailAuthenticationForm` labels the identifier "Email"; `PatientRegistrationForm`
fields `first_name, last_name, email, phone, password1, password2`, `clean_email`
duplicate guard, role forced PATIENT server-side), `accounts/views.py`
(`RegisterView` → `home` on success, auto-login, PATIENT-only — anonymous-only via
`dispatch`), `accounts/urls.py` (namespaced `accounts:*`, `login/logout/register/
password_reset/password_reset_done/password_reset_confirm/password_reset_complete`,
hard-coded success URLs), `accounts/tests.py` (login/invalid/inactive/405-logout/
reset end-to-end contracts), and all eight `accounts/templates/accounts/*` files.

**Contract preserved in the templates:**

- Login: `POST username/password` (+ preserved `next` hidden input), CSRF token,
  shared `_form_errors` / `_field` partials unchanged.
- Registration: every existing field and validation message kept; no role/agent
  selector exists or was added; the "patients only" note retained; CSRF preserved.
- Reset flow: `POST email` → done page; one-time token confirm page (validlink /
  invalid branches) → `POST new_password1/new_password2`; URLs, tokens, messages,
  and the plain-text `password_reset_email.html` / `password_reset_subject.txt`
  untouched (no HTML injected into the email).
- Logout remains a POST-only route (probe re-verified the 405-on-GET contract).
- Shared navbar/footer (base.html) untouched.

## 2. Files changed

| File | Change |
|---|---|
| `accounts/templates/accounts/login.html` | Redesigned as a split editorial layout: left photographic panel (teal scrim + eyebrow + serif line + honest "Illustrative stock photograph — not a Care_Clinic premises" caption), right white form card. Same form contract (`csrf_token`, `_form_errors`, `_field` loop, `next` hidden, novalidate). Register + reset links preserved. |
| `accounts/templates/accounts/register.html` | Related split layout using a different approved stock image; patients-only note kept verbatim; all six fields rendered via the unchanged partial loop; submit button copy "Create account"; back-to-login link. |
| `accounts/templates/accounts/password_reset_form.html` | Single centred `.auth-panel` kept; copy polished ("we will send you a link to choose a new password"); form contract unchanged. |
| `accounts/templates/accounts/password_reset_done.html` | Copy clarified: one-time-use, expiring link, spam-folder hint. |
| `accounts/templates/accounts/password_reset_confirm.html` | Added a reassuring muted lead-in on the valid-link branch; invalid-branch copy polished; both branches' contracts unchanged. |
| `accounts/templates/accounts/password_reset_complete.html` | Unchanged (copy already correct). |
| `accounts/templates/accounts/logged_out.html` | Copy polished ("Your session has ended on this device."); CTA unchanged. |
| `static/css/styles.css` | New "Auth: split editorial panel" section: `.auth-split` grid (1.05fr/0.95fr, `align-items: stretch`), `.auth-visual` (reserved geometry, radius-lg, hairline, deep-teal gradient scrim, overlay quote/caption, `object-fit: cover` crop at `50% 32%`), `.auth-card` (white card, fluid padding clamp). Existing `.auth-panel` / `.auth-links` / `.auth-actions` retained for the simple pages. Responsive: ≤900px stacks photo band (16/10 aspect) above the card; ≤640px fixes the band at 15rem. Reduced-motion unaffected (no new animation). |

No backend files, no URLs, no models, no migrations, no dependencies, no JS
changes. No new image assets — both photographic panels **reuse already-local,
already-licensed, already-manifested images**: `img/home/hero-main.jpg` (login)
and `img/about/waiting-area.jpg` (register), both CORS-free local files, loaded
eager (above-the-fold on the form pages). No hotlinked or Hospic assets.

## 3. Functional regression checks (live, against the running dev server)

CDP probe suite `authqa.mjs` (temp dir `phase-f3`), **54/54 checks passed**:

- Login page: CSRF field, `username`/`password` inputs, "Email"/"Password"
  labels, register + password-reset links, serif h1, photo loads, at 1440/1024/
  768/390 — all pass, zero console errors.
- **Invalid credentials** → Django's standard "Please enter a correct email address
  and password…" non-field alert renders inside the card (browser form submit +
  fetch POST both exercised).
- **Valid login** → redirects home, signed-in navbar (Dashboard / My
  appointments / Log out) visible.
- Registration: duplicate-email error and weak-password validator errors render
  readable in-card; **live POST creates a PATIENT account, auto-signs-in, and
  redirects home**; no role field exists in the rendered form; the patients-only
  note renders.
- Logout: POST → redirect home signed-out (matches `LOGOUT_REDIRECT_URL = "/"`);
  GET logout → 405 (contract preserved; covered by `accounts/tests.py` too).
- Password reset: request → "Check your email" done page; one-time link →
  set-password form → "Password changed"; **login with the new password
  succeeds immediately after**; invalid/expired token link renders the
  "Reset link invalid" page with a re-request action.
- Zoom 150% at 1280px: no horizontal overflow on login.

Full gates after the changes:

- `python manage.py check` → 0 issues.
- `python manage.py makemigrations --check --dry-run` → no changes.
- `pytest` → **227 passed, 1 skipped** (includes all `accounts` auth tests,
  SharedNavigation 9/9, and the complete F2/regression set).
- `git diff --check` → clean (pre-existing CRLF advisories only);
  `git status --porcelain` stays at 77 entries. Nothing staged/committed.
- Existing `liveqa.mjs` suite → **37/37**, zero console errors (navbar/home
  unaffected).

## 4. Responsive results

Verified at **390 / 768 / 1024 / 1440** (device-metric emulation, screenshots
inspected visually — DOM checks alone not relied on):

- 1440: balanced split — photo panel and form card share equal row height
  (`align-items: stretch`). An earlier draft used `align-items: center`, which
  left blank canvas above/below the photo on the taller registration form;
  caught in screenshot review and fixed (login 544px row, register 1077px row,
  both panels equal).
- 1024/768: split holds at 1024; 768 is within the ≤900 stack — photo band tops
  the page, form below.
- 390: photo band (16/10, then fixed 15rem at ≤640) above the card; no input or
  button shrinkage beyond the shared design system; **no horizontal overflow on
  login/register at any tested width**; body-height measurements recorded per
  width in the probe output (`results.json`).
- Simple pages (reset form/done/confirm/complete, logged out): centred card,
  unchanged at all widths.
- Keyboard: Tab reaches skip-link → email input first; focused input outline
  3px visible (existing `:focus-visible` system); labels tied via the unchanged
  `_field` partial; decorative scrim is `aria-hidden`; panel images carry honest
  alt text + captions ("not a Care_Clinic premises") per the imagery rules.

## 5. Screenshot review

Captured with CDP (temp `phase-f3/shots/`) and inspected visually:

1. `f3_login_1440.png` / `f3_login_390.png`, `f3_login_1440_v2.png` (post-fix)
2. `f3_register_1440.png` / `f3_register_390.png`, `f3_register_1440_v2.png`
3. `f3_reset_form_768.png`, `f3_reset_done_768.png`, `f3_reset_confirm_768.png`,
   `f3_reset_invalid_768.png`
4. `f3_login_invalid_1440.png` (in-card credential error)
5. Logged-out page: verified live in the probe (`logged-out POST returns home
   anonymous`, contract per settings); the template keeps the polished
   "You have been logged out" panel for any future no-redirect configuration.

All screenshots reviewed by eye: typography, teal accents, spacing, scrim
legibility (AA against the darkest scrim stop), and honest captions.

## 6. Test-data hygiene

Two temporary QA accounts (`qa-f3@example.com`, `qa-f3-register@example.com`)
were created by `manage.py shell` purely to exercise live login/registration
flows and were **deleted afterwards**; the remaining data
(admin, three demo doctors, the resident patient account) was untouched.
The reset link used for the live end-to-end check was minted with the same
`default_token_generator` Django's email view uses (console email backend in
dev prints the email, which cannot be read from a detached server process).

## 7. Remaining limitations

- The two photos are reused batch-1 assets; bespoke clinic photography would
  further sharpen the pages, subject to the usual consent/manifest rules (and
  must never be presented as clinic premises/staff).
- The `logged_out.html` template is currently unreachable in normal flow
  because `LOGOUT_REDIRECT_URL = "/"` redirects before it renders; it was
  polished anyway and stays as the graceful default (documenting, per scope:
  settings deliberately untouched).
- Overlay quote legibility relies on each panel image's bottom half being
  calm; if newer imagery is swapped in, re-check the scrim contrast
  (currently deep-teal at ≥0.82 alpha over the photo bottom).
- The live probe (54 checks) lives in the temp scratch directory, not the
  repo, consistent with prior phases (`phase-img` scripts); the durable
  regression net for auth remains `accounts/tests.py`.
