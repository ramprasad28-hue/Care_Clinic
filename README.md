# Care_Clinic — Clinic Appointment Management System

Recruitment task for **Anmaya Health Technologies Private Limited**:
a clinic web application with **appointment booking** and **Role-Based Access Control (RBAC)**.

> **Current status: Phase 1 — Requirements & Architecture (complete).**
> The repository contains planning documentation only. No Django project, models, views,
> migrations, templates, or installed dependencies exist yet.

## Purpose

A clinic web application where patients discover doctors and specialities and book
appointments, while four roles — **Patient, Doctor, Receptionist, Admin** — each get a
dashboard with permissions enforced on the backend.

## Technology stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Framework | **Django 5.2 LTS** |
| Database | **MySQL (InnoDB)** |
| Driver | mysqlclient |
| Templating | Django templates + HTML + CSS |
| UI | Bootstrap 5 |
| Interactivity | Vanilla JavaScript (no SPA framework) |
| ORM | Django ORM |
| Config/secrets | `python-dotenv` + `.env` (never committed) |
| Version control | Git / GitHub |
| Testing | pytest + pytest-django (against MySQL) |

No React, Next.js, or microservices — a straightforward, server-rendered Django application.

## Directory / environment layout

| Item | Location |
|---|---|
| Project (this repo) | `C:\Users\Ramprasad\OneDrive\Desktop\Care_Clinic` |
| Virtual environment | `C:\venvs\anmaya-clinic` (deliberately **outside** OneDrive) |
| Git repository root | This folder (dedicated repository, branch `main`) |

## Documentation (`docs/`)

| File | Contents |
|---|---|
| [`docs/requirements.md`](docs/requirements.md) | Confirmed/proposed features, out-of-scope, open employer questions |
| [`docs/architecture.md`](docs/architecture.md) | App structure, booking workflow, RBAC matrix, security, frontend direction |
| [`docs/data-model.md`](docs/data-model.md) | Entities, ERD (Mermaid), constraints, status state machine |
| [`docs/decisions.md`](docs/decisions.md) | Architecture Decision Records (ADR-001…012) |
| [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md) | Phases, testing strategy, security checklist |

## Planned Django apps

`accounts` (auth/roles) · `clinic` (doctors/specialities/availability) ·
`appointments` (slots/bookings/services) · `dashboards` · `website` (public pages) ·
`notifications` (optional, deferred) — plus a `config` project package.

## Setup (to be performed in Phase 2)

> Intentionally not executed yet — this is a planning phase.

```powershell
# 1. Activate the pre-created virtual environment
& C:\venvs\anmaya-clinic\Scripts\Activate.ps1

# 2. Install dependencies (Phase 2)
pip install -r requirements.txt

# 3. Create local environment file
Copy-Item .env.example .env   # then edit values

# 4. Apply migrations and run (Phase 2+)
python manage.py migrate
python manage.py runserver
```

## Safety notices

- A pre-existing Git repository is rooted at `C:\Users\Ramprasad`; this project uses its
  **own repository** and no Git operation is ever run against the parent repo.
- The virtual environment is kept **outside OneDrive** to avoid sync conflicts.
- Real credentials live only in a local `.env` file, never in the repository.

## Roadmap

0. Workspace isolation — **done**
1. Requirements & architecture — **done**
2. Django foundation — next
3. Authentication & RBAC
4. Doctor & speciality management
5. Appointment booking
6. Dashboards
7. Frontend implementation
8. Testing & security
9. Submission preparation

See [`docs/implementation-roadmap.md`](docs/implementation-roadmap.md) for objectives,
tasks, and completion criteria per phase.
