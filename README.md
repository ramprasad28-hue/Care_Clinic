# Care_Clinic — Clinic Appointment Management System

Recruitment task for **Anmaya Health Technologies Private Limited**:
a clinic web application with **appointment booking** and **Role-Based Access Control (RBAC)**.

> **Current status: Phase 3 — Authentication & RBAC (complete).**
> The Django project, custom email-based user model, authentication (login / logout /
> password reset), patient-only registration, role groups, and RBAC primitives are in
> place with 36 passing tests. Public site, booking, and dashboards arrive in later phases.

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

## Project structure (through Phase 3)

```
config/
  settings/  base.py · development.py · production.py
  urls.py · wsgi.py · asgi.py
accounts/    models.py · managers.py · forms.py · views.py · permissions.py
             urls.py · admin.py · tests.py · migrations/
             management/commands/sync_roles.py
             templates/accounts/  login · register · logged_out · password_reset_*
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
```

Privileged roles (Doctor/Receptionist/Admin) are provisioned by an administrator — never
through public registration.

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

### 8. Run tests

```powershell
python manage.py test              # Django test runner
pytest                             # pytest-django (config in pytest.ini)
```

### 9. Start the development server

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
| [`docs/decisions.md`](docs/decisions.md) | Architecture Decision Records (ADR-001…012) |
| [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md) | Phases, testing strategy, security checklist |

## Planned Django apps

`accounts` (auth/roles — **implemented**) · `clinic` (doctors/specialities/availability) ·
`appointments` (slots/bookings/services) · `dashboards` · `website` (public pages) ·
`notifications` (optional, deferred) — plus the `config` project package.

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
4. Doctor & speciality management — next
5. Appointment booking
6. Dashboards
7. Frontend implementation
8. Testing & security
9. Submission preparation

See [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md) for objectives,
tasks, and completion criteria per phase.
