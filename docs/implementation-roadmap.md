# Implementation Roadmap — Care_Clinic

**Phase:** 1 — Roadmap (planning only)
Each phase lists objective, tasks, deliverables, dependencies, and completion criteria.

---

## Phase overview

| # | Phase | Status |
|---|---|---|
| 0 | Workspace isolation | ✅ Complete |
| 1 | Requirements & architecture | ✅ Complete |
| 2 | Django foundation | ✅ Complete |
| 3 | Authentication & RBAC | ✅ Complete |
| 4 | Doctor & speciality management | ⬜ Next |
| 5 | Appointment booking | ⬜ |
| 6 | Dashboards | ⬜ |
| 7 | Frontend implementation | ⬜ |
| 8 | Testing & security hardening | ⬜ |
| 9 | Submission preparation | ⬜ |

---

## Phase 2 — Django foundation
**Objective:** A runnable, configurable Django project with the custom user model in place.
**Tasks:**
- Fix `requirements.txt` Django pin to `>=5.2,<5.3` (ADR-010); verify `mysqlclient` builds (ADR-003).
- `pip install -r requirements.txt` into `C:\venvs\anmaya-clinic`.
- Create `config` project with split settings (`base`/`dev`/`prod`), env loading via `python-dotenv`.
- Create `accounts.User`, set `AUTH_USER_MODEL`, first migrations.
- Base templates, Bootstrap 5 static pipeline, root URLs, `django check`.
**Deliverables:** Running dev server, empty home page, migrations applied.
**Dependencies:** Phase 1; MySQL server available.
**Completion criteria:** `python manage.py check` clean; migrations apply on MySQL; login not yet required.

## Phase 3 — Authentication & RBAC
**Objective:** Identity and authorization backbone.
**Tasks:** Login/logout/password reset; patient registration (role locked to PATIENT);
Groups/Permissions sync; role mixins/decorators; scoped querysets (`for_user`); RBAC tests.
**Deliverables:** Working auth + enforced RBAC.
**Dependencies:** Phase 2.
**Completion criteria:** Unauthorized-access tests pass (see Testing strategy).

**Status (implemented):**
- Login/logout/password-reset via `accounts/urls.py`; email-labelled login form
  (`EmailAuthenticationForm`); console email backend in development.
- Patient-only registration (`PatientRegistrationForm`) — `role` forced to PATIENT server-side
  and never read from input; new patients auto-logged-in.
- `sync_roles` management command creates the four role **Groups**, grants a configurable
  permission set, and reconciles membership with each user's `role`.
- RBAC primitives in `accounts/permissions.py`: `role_required` decorator + `RoleRequiredMixin`
  (anonymous → login redirect; wrong role → 403; superuser/admin always allowed).
- 36 tests green (model, form, registration, auth flows, RBAC primitives, sync command).
- **Deferred:** concrete `for_user` scoped querysets live on the domain models they protect
  (`Appointment.objects.for_user`, `clinic` selectors) and are implemented in Phases 4–5; the
  contract is documented in `accounts/permissions.py`.

## Phase 4 — Doctor & speciality management
**Objective:** Catalog and scheduling configuration.
**Tasks:** `Speciality`, `Doctor`, `AvailabilityRule`, `DoctorLeave` models + admin/CRUD UI;
public listing/detail pages; availability rules UI for doctors.
**Deliverables:** Managed catalog with public pages.
**Dependencies:** Phase 3.
**Completion criteria:** Admin can CRUD; public pages render; leave blocks slots.

## Phase 5 — Appointment booking (core)
**Objective:** Race-safe booking end to end.
**Tasks:** Slot materialization; `book_slot`/`cancel`/`reschedule` services with locking +
constraints; status state machine; booking UI; reference generation; concurrency tests.
**Deliverables:** Working, safe booking flow.
**Dependencies:** Phase 4.
**Completion criteria:** Booking integrity test suite passes, including a concurrency test.

## Phase 6 — Dashboards
**Objective:** Four role-specific dashboards.
**Tasks:** Patient/Doctor/Receptionist/Admin dashboards; check-in; book-on-behalf;
status actions; availability/leave management.
**Deliverables:** All four dashboards functional.
**Dependencies:** Phase 5.
**Completion criteria:** Role flows verified by tests and manual checks.

## Phase 7 — Frontend implementation
**Objective:** Original, accessible UI (design direction in `architecture.md` §8).
**Tasks:** Load and follow the `frontend-design` skill; build public pages and dashboards;
responsive layout; accessibility pass.
**Deliverables:** Polished UI.
**Dependencies:** Phase 6.
**Completion criteria:** Mobile-responsive; keyboard accessible; no copied branding/assets.

## Phase 8 — Testing & security hardening
**Objective:** Prove correctness and safety.
**Tasks:** Full test suite; `web-design-guidelines` audit; `django check --deploy`;
`bandit` / `pip-audit`; fix findings.
**Deliverables:** Green suite + audit report.
**Dependencies:** Phase 7.
**Completion criteria:** All tests pass; no high-severity findings outstanding.

## Phase 9 — Submission preparation
**Objective:** Deliverable package.
**Tasks:** README with setup/credentials/tests; seed-data command; `.env.example`; demo
script; repo hygiene; final documentation review.
**Deliverables:** Submission package.
**Dependencies:** Phase 8.
**Completion criteria:** A reviewer can run the project from the README alone.

---

## Testing strategy

**Tooling:** `pytest` + `pytest-django` + `coverage`, run against **MySQL** (ADR-003).

### Layers
1. **Unit:** model constraints, status state machine, validators, reference generation.
2. **Service:** booking/cancel/reschedule logic, locking behavior, integrity errors.
3. **View/permission:** RBAC matrix, IDOR prevention, anonymous access.
4. **Integration:** full booking flow end to end.

### Essential test cases
- Auth: register (patient-only), login, logout, password reset, inactive user blocked.
- RBAC: Patient A cannot access Patient B's appointment (404, DB unchanged); Doctor cannot
  see another doctor's appointments; Receptionist cannot manage users; anonymous → redirect;
  `role=ADMIN` in registration input is ignored.
- Booking: rejects past dates; rejects unavailable/leave slots; conflict rejected;
  **concurrent double-book attempt → exactly one succeeds**; `IntegrityError` handled.
- Cancellation/reschedule: window enforcement; illegal transitions blocked; slot released.
- Validation: malformed dates/times; missing fields; over-long inputs.

### Manual acceptance
Public booking happy path; each dashboard flow; cancellation window UX; mobile/responsive;
keyboard navigation; direct-URL access checks.

## Security checklist (per phase)
- Secrets only via `.env` (git-ignored); no secrets in code or commits.
- `DEBUG=False` + `ALLOWED_HOSTS` in prod; secure cookie/HSTS flags.
- CSRF on all POST forms; ORM-only queries; server-side validation everywhere.
- Least-privilege DB user; password validators; PII minimization (no clinical data).
- `django check --deploy`, `bandit`, `pip-audit` run before submission.

## Definition of done (project)
1. All §acceptance criteria in `requirements.md` satisfied.
2. Test suite green, including the concurrency test.
3. Documentation (`docs/`) matches the implemented behavior.
4. README enables a clean setup by a third party.
