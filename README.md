# Care_Clinic — Clinic Appointment Management System

Recruitment task for **Anmaya Health Technologies Private Limited**:
a clinic web application with **appointment booking** and **Role-Based Access Control (RBAC)**.

> **Current status: Phase 6 — Role-Based Dashboards (complete).**
> Builds on the Django project, custom email-based user model, authentication (login /
> logout / password reset), patient-only registration, role groups, RBAC primitives, the
> clinic catalog (`clinic`), the public site (`website`), and the race-safe booking flow
> (`appointments`). Phase 6 adds the `dashboards` app: a role-routed landing page and
> Patient / Doctor / Receptionist / Admin dashboards with shared search, filtering and
> pagination — **205 passing tests** (one MySQL-only concurrency test skipped on SQLite).

## Purpose

A clinic web application where patients discover doctors and specialities and book
appointments, while four roles — **Patient, Doctor, Receptionist, Admin** — each get a
dashboard with permissions enforced on the backend.

## Technology stack & verified versions

| Layer | Choice | Version (installed) |
|---|---|---|
| Language | Python | **3.12.0** |
| Framework | **Django 5.2 LTS** | **5.2.18** |
| Database | **MySQL (InnoDB)** | driver `mysqlclient 2.3.0` installed — *see Database note* |
| Templating | Django templates + HTML + CSS | — |
| UI | Bootstrap 5 (full design in Phase 7) | — |
| Interactivity | Vanilla JavaScript (no SPA framework) | — |
| ORM | Django ORM | — |
| Config/secrets | `python-dotenv` + `.env` (never committed) | python-dotenv 1.2.4 |
| Version control | Git / GitHub | — |
| Testing | pytest + pytest-django | pytest 8.4.2, pytest-django 4.14.0 |

No React, Next.js, or microservices — a straightforward, server-rendered Django application.

## Directory / environment layout

| Item | Location |
|---|---|
| Project (this repo) | `C:\Users\Ramprasad\OneDrive\Desktop\Care_Clinic` |
| Virtual environment | `C:\venvs\anmaya-clinic` (deliberately **outside** OneDrive) |
| Git repository root | This folder (dedicated repository, branch `main`) |

## Project structure (through Phase 6)

```
config/
  settings/  base.py · development.py · production.py
  urls.py · wsgi.py · asgi.py
accounts/    models.py · managers.py · forms.py · views.py · permissions.py
             urls.py · admin.py · tests.py · migrations/
             management/commands/sync_roles.py
             templates/accounts/  login · register · logged_out · password_reset_*
clinic/      models.py (Speciality, Doctor, AvailabilityRule, DoctorLeave) · forms.py
             views.py · urls.py · admin.py · selectors.py · tests.py · migrations/
             management/commands/seed_clinic.py
             templates/clinic/  availability_* · leave_*
appointments/ models.py (AppointmentSlot, Appointment) · slot_generation.py · services.py
             selectors.py · forms.py · views.py · urls.py · admin.py · tests.py
             migrations/ · management/commands/generate_slots.py
             templates/appointments/  appointment_list · appointment_detail
                                      appointment_book · appointment_cancel
                                      appointment_reschedule
dashboards/  selectors.py · forms.py · views.py · urls.py · tests.py  (no models/migrations)
             templates/dashboards/  patient_dashboard · doctor_dashboard
                                    receptionist_dashboard · receptionist_book
                                    admin_dashboard · no_dashboard
                                    _appointment_table · _filters · _pagination
website/     views.py · urls.py · apps.py · tests.py
             templates/website/  speciality_list · speciality_detail
                                 doctor_list · doctor_detail
templates/   base.html · home.html
static/      css/styles.css
manage.py · pytest.ini · requirements.txt · .env.example · docs/
```

## Setup

### 1. Python and virtual environment

Python **3.12** is required. The dedicated virtual environment lives **outside OneDrive**:

```powershell
# Activate the virtual environment
& C:\venvs\anmaya-clinic\Scripts\Activate.ps1
python --version          # expect Python 3.12.x
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

This installs Django 5.2 LTS, `mysqlclient`, `python-dotenv`, and the test/security tooling.
All packages go into the virtual environment only — never install globally.

### 3. Environment configuration

```powershell
Copy-Item .env.example .env
# then edit .env with your local values
```

`.env` is git-ignored and must never be committed. Variables (see `.env.example`):

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django secret key (generate a long random value) |
| `DJANGO_DEBUG` | `True` locally, `False` in production |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames |
| `DB_ENGINE` | `mysql` (default) or `sqlite` (documented local fallback) |
| `DATABASE_NAME` | Database name |
| `DATABASE_USER` | Database user |
| `DATABASE_PASSWORD` | Database password |
| `DATABASE_HOST` | Database host (default `127.0.0.1`) |
| `DATABASE_PORT` | Database port (default `3306`) |

**Settings modules:** `config.settings.development` (default, `manage.py`) and
`config.settings.production` (enforces a real `DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS`
and turns on HTTPS/HSTS/secure cookies). `wsgi.py`/`asgi.py` default to production.

### 4. Database creation and connection

The intended primary database is **MySQL 8 with InnoDB** (ADR-003). Create the database and
a dedicated, least-privilege user (run as a MySQL admin):

```sql
CREATE DATABASE care_clinic CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'care_clinic_user'@'localhost' IDENTIFIED BY '<strong-password>';
GRANT ALL PRIVILEGES ON care_clinic.* TO 'care_clinic_user'@'localhost';
FLUSH PRIVILEGES;
```

Use `ENGINE=InnoDB` (the default) so row-level locking and foreign keys are available. Then
set the `DATABASE_*` values in `.env` and keep `DB_ENGINE=mysql`.

> **Local fallback (documented):** if MySQL credentials are not available, set
> `DB_ENGINE=sqlite` in `.env`. This creates `db.sqlite3` and is suitable **only** for
> framework checks and tests. It does **not** validate MySQL/InnoDB behavior — migrations
> must be re-verified against MySQL before delivery.

### 5. Migrations

```powershell
python manage.py makemigrations   # generate (already committed for accounts)
python manage.py migrate          # apply
python manage.py makemigrations --check --dry-run   # assert no missing migrations
```

### 6. Create an administrator

```powershell
python manage.py createsuperuser   # login is by email
python manage.py sync_roles        # create role Groups + permissions (idempotent)
python manage.py seed_clinic       # create synthetic specialities + doctors (idempotent)
python manage.py generate_slots    # materialize bookable slots (idempotent; --days N)
```

Privileged roles (Doctor/Receptionist/Admin) are provisioned by an administrator — never
through public registration. `seed_clinic` also provisions three **DOCTOR-role demo users**
with unusable passwords (they cannot log in) purely to populate the public catalog.

### 7. Authentication & RBAC (Phase 3)

| Route | Purpose |
|---|---|
| `/accounts/login/` | Log in with **email** + password |
| `/accounts/logout/` | Log out (POST only) |
| `/accounts/register/` | Patient self-registration (role forced to `PATIENT`) |
| `/accounts/password-reset/` | Request a reset link (printed to console in dev) |

RBAC primitives live in `accounts/permissions.py`:
`role_required(*roles)` decorator and `RoleRequiredMixin` for class-based views — anonymous
users are redirected to login, wrong-role users get HTTP 403, and superusers/admins always
pass. `python manage.py sync_roles [--dry-run]` keeps role groups and permissions aligned.

### 8. Public site & clinic management (Phase 4)

**Public pages** (`website` app, anonymous access):

| Route | Purpose |
|---|---|
| `/` | Home — active specialities and accepting doctors |
| `/specialities/` · `/specialities/<slug>/` | List / detail of **active** specialities |
| `/doctors/` (optionally `?speciality=<slug>`) | List of **accepting** doctors, filterable |
| `/doctors/<slug>/` | Doctor detail with weekly availability |

Inactive specialities, non-accepting or unknown doctors, and unknown slugs return **404**.
Only doctors whose user and speciality are active and who are accepting appointments are
shown (`Doctor.objects.public()`).

**Doctor self-service** (`clinic` app, DOCTOR role only) — ownership is enforced server-side,
so a doctor can only ever see or change their own rows:

| Route | Purpose |
|---|---|
| `/clinic/doctor/availability/` | List weekly availability windows |
| `/clinic/doctor/availability/add/` · `<pk>/edit/` · `<pk>/delete/` | Manage a window |
| `/clinic/doctor/leave/` | List leave periods |
| `/clinic/doctor/leave/add/` · `<pk>/delete/` | Manage leave |

Availability windows are validated so end time is after start time and windows never overlap;
leave end date cannot precede its start date. `Speciality`/`Doctor` are managed in the Django
admin by the **Administrator** role; `AvailabilityRule`/`DoctorLeave` in the admin are scoped
to the logged-in doctor.

### 9. Appointment booking (Phase 5)

**`appointments` app** — concrete bookable slots generated from availability and bookings that
flow through transactional services:

| Route | Purpose |
|---|---|
| `/appointments/book/<doctor-slug>/` | Patient books a slot (optional `?date=YYYY-MM-DD`) |
| `/appointments/` | Appointment list (`?scope=upcoming|past`), scoped to the user |
| `/appointments/<reference>/` | Appointment detail (e.g. `CC-2026-000123`) |
| `/appointments/<reference>/cancel/` | Confirm-and-cancel page |
| `/appointments/<reference>/reschedule/` | Move a booking to another slot |

- **Slot generation:** `generate_slots` materializes `AppointmentSlot` rows from active
  `AvailabilityRule` windows over a rolling horizon, honoring the rule/doctor slot length and
  skipping leave and past intervals. It is idempotent and preserves existing `BOOKED` slots.
- **Race-safe booking:** every mutation runs in `transaction.atomic()` with
  `select_for_update()` on the slot row. One active booking per slot is guaranteed by the
  database (nullable `OneToOneField` + release-on-cancel — ADR-017), not an app-only check.
- **Ownership:** all record lookups go through `Appointment.objects.for_user`, so an
  unauthorized reference returns **404**. The actor's role is read from the session.
- **Status state machine:** `REQUESTED → CONFIRMED → CHECKED_IN → COMPLETED`, plus `CANCELLED`
  and `NO_SHOW`; illegal transitions are rejected. Cancelling never deletes the record — the
  slot is released and history is kept. Patients may self-cancel/reschedule up to **24 h**
  before the slot (staff, until it starts) — provisional (ADR-018).

### 10. Dashboards (Phase 6)

The `dashboards` app adds a role-routed landing page and four dashboards. It has **no
models and no migrations** — it composes existing data and delegates all state changes to
`appointments.services` (ADR-019).

| Route | Access | Purpose |
|---|---|---|
| `/dashboard/` | any authenticated user | Route to the dashboard for the user's role |
| `/dashboard/patient/` | Patient | Own upcoming + past appointments |
| `/dashboard/doctor/` | Doctor | Own schedule: today / upcoming / past + status actions |
| `/dashboard/receptionist/` | Receptionist | Clinic-wide, filterable list + link to book |
| `/dashboard/receptionist/book/` | Receptionist | Book a slot on behalf of a patient |
| `/dashboard/admin/` | Admin | Aggregated statistics + filterable list |
| `/dashboard/appointments/<reference>/status/` | Doctor/Receptionist/Admin | Apply a permitted status transition (**POST** only) |

- **Routing & safety:** `/dashboard/` reads the role from the **session user** (never the
  request body) and redirects; anonymous users go to login, and an unrecognised role renders
  a safe "no dashboard" page. Every dashboard is gated by `RoleRequiredMixin`.
- **Ownership first:** list views call `Appointment.objects.for_user` *before* applying
  filters, and the doctor dashboard is scoped to the caller's own `Doctor` profile — a
  foreign reference returns **404** (IDOR prevention).
- **Search/filter/pagination:** optional `scope` (`upcoming`/`today`/`past`/`all`), `date`,
  `status`, `doctor`, `patient` and `reference` filters; malformed values degrade to "no
  filter" instead of erroring, and invalid page numbers fall back safely
  (`Paginator.get_page`). Filters are preserved across pagination links.
- **Status actions** are shown only when `services.can_update_status` allows them and always
  route through `services.transition_status`; book-on-behalf validates the submitted
  patient/doctor through `ModelChoiceField`s before calling `services.book_slot`.

### 11. Run tests

```powershell
python manage.py test              # Django test runner
pytest                             # pytest-django (config in pytest.ini)
```

The MySQL-only concurrency test is skipped on SQLite; see
[`docs/mysql-validation.md`](docs/mysql-validation.md) for the exact MySQL/InnoDB procedure.

### 12. Start the development server

```powershell
python manage.py runserver
# Homepage: http://127.0.0.1:8000/     Admin: http://127.0.0.1:8000/admin/
```

## Documentation (`docs/`)

| File | Contents |
|---|---|
| [`docs/requirements.md`](docs/requirements.md) | Confirmed/proposed features, out-of-scope, open employer questions |
| [`docs/architecture.md`](docs/architecture.md) | App structure, booking workflow, RBAC matrix, security, frontend direction |
| [`docs/data-model.md`](docs/data-model.md) | Entities, ERD (Mermaid), constraints, status state machine |
| [`docs/decisions.md`](docs/decisions.md) | Architecture Decision Records (ADR-001…019) |
| [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md) | Phases, testing strategy, security checklist |
| [`docs/mysql-validation.md`](docs/mysql-validation.md) | Exact MySQL/InnoDB validation + concurrency procedure |

## Planned Django apps

`accounts` (auth/roles) · `clinic` (doctors/specialities/availability) ·
`website` (public pages) · `appointments` (slots/bookings/services) ·
`dashboards` (role dashboards) — **all implemented** — plus the `config` package and
`notifications` (optional, deferred).

## Safety notices

- A pre-existing Git repository is rooted at `C:\Users\Ramprasad`; this project uses its
  **own repository** and no Git operation is ever run against the parent repo.
- The virtual environment is kept **outside OneDrive** to avoid sync conflicts.
- Real credentials live only in a local `.env` file, never in the repository or logs.

## Roadmap

0. Workspace isolation — **done**
1. Requirements & architecture — **done**
2. Django foundation — **done**
3. Authentication & RBAC — **done**
4. Doctor & speciality management — **done**
5. Appointment booking — **done**
6. Dashboards — **done**
7. Frontend implementation
8. Testing & security
9. Submission preparation

See [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md) for objectives,
tasks, and completion criteria per phase.
