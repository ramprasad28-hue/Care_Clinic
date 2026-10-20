# Phase 7.5 — Phase 7 (Authentication Pages) — Report

> **Date:** 2026-10-18
> **Project:** `C:\Users\Ramprasad\OneDrive\Desktop\Care_Clinic`
> **Phase:** 7.5 / Phase 7 — bring the authentication surfaces (login, patient registration,
> logout, and the four-step password-reset flow) into the premium-editorial system established
> on the homepage and carried through the public pages.
> **Application files changed:** `accounts/templates/accounts/login.html`,
> `register.html`, `logged_out.html`, `password_reset_form.html`, `password_reset_done.html`,
> `password_reset_confirm.html`, `password_reset_complete.html`, `static/css/styles.css`.
> **Deliverable:** this report (`docs/phase-7.5-authentication-report.md`).
> **Nothing committed or pushed.** No backend, model, view, form, URL, migration, setting,
> dependency or JavaScript file was changed.
> **Skills applied:** `design-taste-frontend` (project-local, `.agents/skills/design-taste-frontend`)
> for the house rules; `frontend-design`, `web-design-guidelines`.

---

## 1. Scope

The Phase 7.5 plan (`docs/phase-7.5-implementation-plan.md` §"Phase 7") names the auth templates
plus `static/css/styles.css` and the intent: *"calm `.auth-panel`, correct input radius, inline
errors, consistent `.auth-actions`"*, with **"Introduce/Replace: none."** The task brief additionally
required inspecting **every** auth template, "not only login and registration".

| Surface | Route | Method | In scope | Covered |
|---|---|---|:--:|:--:|
| Login | `/accounts/login/` | GET/POST | yes | ✅ |
| Register (patients only) | `/accounts/register/` | GET/POST | yes | ✅ |
| Logout | `/accounts/logout/` | POST | yes | ⚠️ route redirects to `/` (see §7) |
| Reset request | `/accounts/password-reset/` | GET/POST | yes | ✅ |
| Reset sent | `/accounts/password-reset/done/` | GET | yes | ✅ |
| Reset confirm (valid link) | `/accounts/reset/<uidb64>/<token>/` | GET | yes | ✅ |
| Reset confirm (invalid link) | `/accounts/reset/<uidb64>/<token>/` | GET | yes | ✅ |
| Reset complete | `/accounts/reset/done/` | GET | yes | ✅ |
| Reset email / subject | — | — | no (plain-text email, not UI) | untouched |

All 7 page templates are covered. `password_reset_email.html` and `password_reset_subject.txt` are
plain-text email output, not rendered UI, so they are out of scope and unchanged.

**No new primitives were introduced** (plan: *"Introduce: none"*). The change reuses the existing
`.section-rule` (Phase 2) and the established `.auth-panel` / `.container--form` / `_field.html` /
`_form_errors.html` / `.form-actions` / `.auth-links` / `.auth-actions` structures.

---

## 1a. Files changed

| File | Change |
|---|---|
| `accounts/templates/accounts/login.html` | Added `<span class="section-rule" aria-hidden="true">` above the `h1`. |
| `accounts/templates/accounts/register.html` | Same rule lead-in. |
| `accounts/templates/accounts/logged_out.html` | Same rule lead-in. |
| `accounts/templates/accounts/password_reset_form.html` | Same rule lead-in. |
| `accounts/templates/accounts/password_reset_done.html` | Same rule lead-in. |
| `accounts/templates/accounts/password_reset_complete.html` | Same rule lead-in. |
| `accounts/templates/accounts/password_reset_confirm.html` | Rule lead-in in **both** branches (valid + invalid link). |
| `static/css/styles.css` | `.auth-panel` flattened (shadow removed) + generous padding; new `.auth-panel .section-rule` spacing. |
| `docs/phase-7.5-authentication-report.md` | This report (new). |

No shared partial was modified (`_field.html` / `_form_errors.html` are owned by Phase 3 and are
used by booking and dashboards). No other parent template was touched.

---

## 2. Design direction applied

The public pages (Phases 4–6) open every content block with a short teal rule under a serif
heading. The auth panels had the same serif `h1` inside a bordered card, but no rule and a
drop shadow that read as a generic "SaaS login card". Phase 7 makes the auth surfaces read as
part of the same editorial system:

- **Rule lead-in** — the same decorative `<span class="section-rule" aria-hidden="true">`
  (40 × 2 px, `--brand-600`) sits directly above every `h1`, matching the public page-heads.
- **Calm panel** — the `box-shadow: var(--shadow-sm)` was removed, leaving a single hairline
  `1px solid var(--line)` border and the shared `--radius` (12 px). This matches the now-flat
  editorial cards (Phase 3) and the flat filter strip (Phase 6): surfaces are defined by rules
  and borders, not lifted by shadows.
- **More deliberate whitespace** — panel padding grew from `var(--sp-6)` (2 rem, uniform) to
  `var(--sp-7) var(--sp-6)` (3 rem vertical / 2 rem horizontal) and the block margin from
  `var(--sp-4)` to `var(--sp-6)`, giving the short auth forms room to breathe.
- **Everything else reused as-is** — labels, required asterisks, help text, inline errors,
  `.form-actions` block buttons, `.auth-links` ruled link row, and the serif heading all keep
  their existing treatment, so the panels stay visually identical across all seven pages.

No copy, imagery, trust badges, statistics or assurances were added. The only markup added is one
decorative, `aria-hidden` rule per page.

---

## 3. Template changes (identical one-line lead-in per page)

```diff
  <section class="auth-panel" aria-labelledby="login-heading">
+     <span class="section-rule" aria-hidden="true"></span>
      <h1 id="login-heading">Log in</h1>
```

`password_reset_confirm.html` gets the rule in both conditional branches so the invalid-link
screen (`Reset link invalid`) is styled identically to the valid one:

```diff
  {% if validlink %}
+     <span class="section-rule" aria-hidden="true"></span>
      <h1 id="reset-confirm-heading">Set a new password</h1>
  ...
  {% else %}
+     <span class="section-rule" aria-hidden="true"></span>
      <h1 id="reset-confirm-heading">Reset link invalid</h1>
```

Everything else in every template is byte-identical: `aria-labelledby`, `{% csrf_token %}`, the
`_form_errors.html` include, the `{% for field in form %}` loop over `_field.html`, the hidden
`next` input on login, the button labels, and all `{% url %}` names.

---

## 3. CSS refinements (in place, tokens only)

| Selector | Before | After |
|---|---|---|
| `.auth-panel` | `margin: var(--sp-4) auto`; `padding: var(--sp-6)`; `box-shadow: var(--shadow-sm)` | `margin: var(--sp-6) auto`; `padding: var(--sp-7) var(--sp-6)`; **no `box-shadow`**; border/radius/background unchanged |
| `.auth-panel .section-rule` | (none) | new: `margin-bottom: var(--sp-3)` (12 px) — applies only where a rule is present |
| `@media (max-width: 640px) .auth-panel` | `padding: var(--sp-5)` | unchanged (`sp-5`, 1.5 rem — keeps the panel from feeling cramped on phones) |

No new colour, font, radius, shadow or motion token was added. `.form`, `.field*`, `input` radius
(`var(--radius)`), `.form-actions`, `.auth-links` and `.auth-actions` are unchanged; `.auth-actions`
already existed in the stylesheet (it is now used by `logged_out.html` / `password_reset_complete.html`).

---

## 3a. Accessibility (spec §K)

Measured on the live pages (DOM/CSSOM, not visual):

- **Labels associated:** every input has a `<label for>` whose `for` equals the control `id`
  (e.g. `for="id_username"` ↔ `id="id_username"`), verified on all seven forms.
- **Required indicators:** required fields carry the native `required` attribute (announced by
  screen readers) plus the existing visual `*` marker (`aria-hidden`, so it is not double-read).
  In `register` the required fields are Email / Password / Password confirmation; first name,
  last name and phone are optional and correctly have no marker.
- **Input types:** `type="password"` on every password field (login 1, register 2, reset-confirm 2);
  `type="email"` for email, `type="tel"` for phone.
- **Autocomplete:** `username`/`current-password` on login, `new-password` on reset + register,
  `email`/`given-name`/`family-name`/`tel` on register.
- **Errors:** non-field errors render in `.form-alerts .message.error` with `role="alert"`;
  field errors render inline in `.field__error`. A wrong login produces exactly 1 alert; an empty
  register submit produces 3 inline field errors (one per required field).
- **Heading hierarchy:** exactly one `h1` per page, on every page and every state (including both
  reset-confirm branches); no skipped levels.
- **Focus / reduced motion:** the shared `:focus-visible` ring and `input:focus` treatment are
  unchanged; with `prefers-reduced-motion: reduce` the media matches and transition durations
  collapse to `1e-06s`.
- **Link names:** "Log in", "Create a patient account", "Forgot your password?", "Back to log in",
  "Request a new reset link" — all descriptive.

---

## 4. Responsive verification (390 / 768 / 1024 / 1440)

| Check | Result |
|---|---|
| Horizontal overflow | **0 px** on every route × every width (28 route/width passes) |
| Panel | present, `max-width: 480px`, centered, `1px solid rgb(229,231,235)`, `radius 12px`, `box-shadow: none`, `padding 48px 32px` |
| Rule | present in every panel, `40 × 2px`, `rgb(14,165,168)` (`--brand-600`), `margin-bottom 12px` |
| Primary action | full-width `btn--primary`, `min-height 46px` (≥ 44 px touch target) |
| Console errors | **0** on every pass |
| JS disabled | register page still renders (`h1 = 1`, 6 fields, rule present, no overflow) |

---

## 5. Functional preservation (spec §K)

- **Behaviour unchanged.** Diffs are limited to one added decorative span per page + CSS. No view,
  form, model, URL, setting, migration or test was touched.
- **Registration string preserved.** The exact copy
  `Registration is for <strong>patients only</strong>.` is intact
  (asserted by `accounts/tests.py`, line 163).
- **Flow preserved.** Login via email → redirect home; `next` hidden field kept; patient
  registration sets the PATIENT role and redirects home; password reset request → done → confirm
  → complete, all under the same namespaced URL names; CSRF tokens intact; logout is POST-only.
- **Not weakened.** No password validators, auth protection, redirect target or role-assignment
  logic was altered. Password inputs keep `type="password"`.
- **No invented content** — no testimonials, statistics, guarantees, trust badges, imagery, or
  new marketing prose were added.

---

## 6. Validation

| Command | Result |
|---|---|
| `python manage.py check` | `System check identified no issues (0 silenced).` |
| `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| `python manage.py test` | **OK**, 205 tests, `skipped=1` (242.51 s) |
| `pytest -q` | **204 passed**, 1 skipped (244.01 s) |
| `git diff --check` | exit 0 (only pre-existing `core.autocrlf` LF→CRLF advisories) |
| CSS brace balance | `{` 389 / `}` 389 |

Environment: `C:\venvs\anmaya-clinic\Scripts\python.exe` (Python 3.12), Django development settings.
The tracebacks printed mid-run are the expected `PermissionDenied` / 404 negative-path tests.

---

## 6a. Browser verification

Tooling: the repository's own `design-taste-frontend` CDP driver
(`.agents/skills/design-taste-frontend/scripts/lib/cdp.mjs`) driving installed Chrome
(`C:\Program Files\Google\Chrome\Application\chrome.exe`, Node v22.23.1); live dev server on
`http://127.0.0.1:8017/`. Script: `qa-phase7.mjs`; screenshots + JSON: `.taste-skill/inspect/phase7/`.

Routes driven: `login`, `register`, `password-reset`, `password-reset/done`,
`reset/<bogus>/<bogus>` (invalid branch), `reset/<uid>/<token>` (**valid branch**),
`reset/done` — each at 390 / 768 / 1024 / 1440 (28 passes), plus two error-state passes
(wrong login, empty register submit) and reduced-motion + JS-disabled passes.

The valid reset link was generated locally with `default_token_generator.make_token()` for an
existing account and pointed at directly — **no reset email was sent** during QA.

**Perceptual review limitation.** Screenshots were captured as required, but the model answering
this task **cannot read image input**, so no visual/perceptual judgement of them was performed.
Every finding above is a quantitative DOM/CSSOM measurement. This is stated rather than claiming a
visual review that did not happen.

*Tooling note:* the CDP `browser.close()` again did not let Node exit cleanly on this machine (the
shell hit its timeout after all output and `report.json` were written) — a harness quirk, not a
page error (page-level `consoleErrors` were empty).

---

## 7. Unresolved issues / observations (reported, not fixed)

1. **`accounts/logged_out.html` is currently unreachable.** The logout route sets
   `template_name="accounts/logged_out.html"` but no `next_page`, while
   `settings.LOGOUT_REDIRECT_URL = "/"` (`config/settings/base.py:99`) takes precedence — so
   `POST /accounts/logout/` issues a 302 to `/` and never renders the template. Confirmed with the
   Django test client (`status 200`, final path `/`, no auth-panel in the body). Changing this
   would require a settings/URL change (a behaviour change), so it was **not** done here; the
   template was still restyled so it is consistent if it is ever routed.
2. **Field errors are not programmatically linked to inputs** (`aria-describedby` / `aria-invalid`
   are absent). This lives in the shared partial `templates/partials/_field.html`, which is owned
   by Phase 3 and used by booking and dashboards, so it was left untouched to respect Phase 7
   scope. Required-ness is still announced via the native `required` attribute. Recommended as a
   later cross-cutting accessibility pass.
3. **Documentation gaps** (same as reported in Phase 6): `docs/phase-7.5-homepage-hero-report.md`
   is missing; there is no standalone Phase 5 (home bands) report; `docs/implementation-roadmap.md`
   lacks the 7.5 stage rows.

---

## 8. Git safety

`git status` was inspected; no `git reset` / `git clean` / restore / checkout was run; nothing was
staged, committed, pushed or branched. All pre-existing tracked modifications and untracked files
were preserved. Phase 7 touched only the seven auth templates, `static/css/styles.css`, and this
report. Work stops here for review.
