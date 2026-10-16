# Care_Clinic — Clinic Appointment Management System

Recruitment task for **Anmaya Health Technologies Private Limited**:
a clinic web application with **appointment booking** and **Role-Based Access Control (RBAC)**.

> **Current status: Phase 4 — Doctor & Speciality Management (complete).**
> Builds on the Django project, custom email-based user model, authentication (login /
> logout / password reset), patient-only registration, role groups, and RBAC primitives.
> Phase 4 adds the clinic catalog (`clinic` app) and the public site (`website` app):
> specialities, doctors, doctor self-service availability & leave, and admin — with
> **94 passing tests**. Appointment booking and dashboards arrive in later phases.

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

## Project structure (through Phase 4)

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

### 9. Run tests

```powershell
python manage.py test              # Django test runner
pytest                             # pytest-django (config in pytest.ini)
```

### 10. Start the development server

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
| [`docs/decisions.md`](docs/decisions.md) | Architecture Decision Records (ADR-001…015) |
| [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md) | Phases, testing strategy, security checklist |

## Planned Django apps

`accounts` (auth/roles) · `clinic` (doctors/specialities/availability) ·
`website` (public pages) — **all implemented** — then `appointments` (slots/bookings/
services) · `dashboards` · `notifications` (optional, deferred) — plus the `config` package.

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
5. Appointment booking
6. Dashboards
7. Frontend implementation
8. Testing & security
9. Submission preparation

See [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md) for objectives,
tasks, and completion criteria per phase.
