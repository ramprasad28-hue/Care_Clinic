# Anmaya Health Clinic — Appointment Management System

Recruitment task for **Anmaya Health Technologies Private Limited**:
a clinic web application with **appointment booking** and **Role-Based Access Control (RBAC)**.

> Current status: **Phase 0 — Workspace Isolation (complete).**
> This repository contains workspace scaffolding only. No application code,
> no Django project, no models, no migrations, and no installed dependencies yet.

## Purpose

Provide a clinic web application where patients can discover doctors and
specialities and book appointments, while four roles — **Patient, Doctor,
Receptionist, Administrator** — each get a dashboard with permissions enforced
on the backend.

## Proposed technology stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Framework | Django (server-rendered) |
| Database | MySQL (provisional; confirm with employer) |
| Templating | Django templates + HTML + CSS |
| UI | Bootstrap 5 |
| Interactivity | Vanilla JavaScript (no SPA framework) |
| ORM | Django ORM |
| Config/secrets | `python-dotenv` + `.env` (never committed) |
| Version control | Git (dedicated repository) |
| Testing | pytest + pytest-django |

No React/Next.js is introduced; the requirement is a straightforward Django app.

## Directory / environment layout

| Item | Location |
|---|---|
| Project (this repo) | `C:\Users\Ramprasad\OneDrive\Desktop\Anmaya Clinic` |
| Virtual environment | `C:\venvs\anmaya-clinic` (deliberately **outside** OneDrive) |
| Git repository root | This folder (dedicated, nested repo) |

## Files in this phase

- `.gitignore` — excludes secrets, bytecode, venvs, local DBs, media, IDE/OS files.
- `.env.example` — documented placeholders only, no real credentials.
- `requirements.txt` — proposed Django/MySQL dependencies (not installed yet).
- `README.md` — this document.

## Setup (to be performed in later phases)

> Intentionally not executed in Phase 0.

```powershell
# 1. Activate the pre-created virtual environment
& C:\venvs\anmaya-clinic\Scripts\Activate.ps1

# 2. Install dependencies (Phase 2)
pip install -r requirements.txt

# 3. Create local environment file
Copy-Item .env.example .env   # then edit values
```

## Safety notices

- The project lives inside the Windows home directory. A pre-existing Git
  repository is rooted at `C:\Users\Ramprasad`; this project uses its **own
  nested repository** and no Git operation is ever run against the parent repo.
- The virtual environment is kept **outside OneDrive** to avoid sync conflicts.
- Real credentials must live only in a local `.env` file.

## Roadmap

0. Workspace isolation — **done**
1. Requirements & architecture — next
2. Django foundation
3. Authentication & RBAC
4. Doctor & speciality management
5. Appointment booking
6. Dashboards
7. Frontend implementation
8. Testing & security
9. Submission preparation
