# Architecture Decision Records — Care_Clinic

**Phase:** 1 — Decisions (planning only)
Each record: Context → Decision → Consequences.

---

## ADR-001 — Modular monolith with server-rendered pages

**Context:** Recruitment task needs appointment booking + RBAC for a clinic.
**Decision:** One Django project, server-rendered Django Templates + Bootstrap. No SPA,
no React/Next.js, no microservices.
**Consequences:** Fast to build, easy to review, minimal infrastructure. Frontend
interactivity is limited to small vanilla-JS enhancements (e.g. slot fetching).

## ADR-002 — Django 5.2 LTS

**Context:** Employer brief specifies Django 5.2 LTS. Existing `requirements.txt` pins
`Django>=5.0,<5.2`, which **excludes** 5.2.
**Decision:** Use **Django 5.2 LTS**.
**Consequences:** `requirements.txt` must be corrected to `Django>=5.2,<5.3` in Phase 2
before installation. Flagged as an open action (see §Open Issues).

## ADR-003 — MySQL (InnoDB) as the primary database

**Context:** Employer stack specifies MySQL with InnoDB; booking integrity needs real
row locking.
**Decision:** Target MySQL/InnoDB via `mysqlclient`. Tests run against MySQL so that
`SELECT ... FOR UPDATE` and unique-constraint behavior are exercised realistically.
**Consequences:** Requires a MySQL server for the test suite. If `mysqlclient` cannot be
built on Windows, fall back to `PyMySQL` with an explicit driver bootstrap — document the
swap in `decisions.md` and update `.env.example`.

## ADR-004 — Single custom `User` with a `role` field

**Context:** Four roles; public registration must create patients only.
**Decision:** One `accounts.User(AbstractUser)` with a `role` choices field, set as
`AUTH_USER_MODEL` **before the first migration**. Django Groups/Permissions provide coarse
capabilities; role drives routing and queryset scoping.
**Consequences:** No migration pain later. Role escalation is prevented by never accepting
`role` from public input and by admin-only provisioning. Cannot easily give a user two
roles (acceptable — roles are mutually exclusive here).

## ADR-005 — Concrete `AppointmentSlot` rows

**Context:** Need an unambiguous, race-safe way to prevent double booking.
**Decision:** Materialize concrete slots (doctor + date + start/end) with a unique
constraint; an appointment claims a slot via a OneToOne FK.
**Consequences:** Simple, DB-enforced integrity. Requires a materialization step
(management command or lazy generation) for a rolling window (e.g. 30 days ahead).

## ADR-006 — Transactional service layer with row locking

**Context:** Concurrent requests must not both book the same slot.
**Decision:** Booking goes through `appointments.services.book_slot()` using
`transaction.atomic()` + `select_for_update()` on the slot row, with `IntegrityError`
handled as a friendly "slot taken" error.
**Consequences:** Correctness does not depend on view code. All writes (book, cancel,
reschedule) follow the same pattern. Slightly more code than inline views.

## ADR-007 — Backend-only authorization (scoped querysets + role gates)

**Context:** Patients must not see others' appointments; doctors see only their schedule.
**Decision:** Authorization enforced in querysets (`for_user(user)`), object lookups on
scoped querysets (404 for unauthorized IDs), role mixins/decorators on views, and
re-checks inside services. UI hiding is cosmetic only.
**Consequences:** Prevents IDOR and privilege escalation. Every new view must use the
scoped queryset — enforced by code review and tests.

## ADR-008 — Defer unrequested modules

**Context:** Employer asked only for booking + RBAC + "necessary features".
**Decision:** No payments, prescriptions, medical records, lab results, or insurance in v1.
**Consequences:** Keeps v1 focused and reviewable. Data model deliberately stores no
clinical content (PII minimization).

## ADR-009 — Notifications deferred and interface-based

**Context:** Reminders are useful but unrequested and require a provider.
**Decision:** Design a minimal notification interface; implement in-app notifications only
if time permits; email/SMS pluggable later. Not on the v1 critical path.
**Consequences:** No external dependencies in v1; appointment flow stays self-contained.

## ADR-010 — `requirements.txt` alignment (open action for Phase 2)

**Context:** Current pin `Django>=5.0,<5.2` conflicts with the mandated Django 5.2 LTS.
**Decision:** Update to `Django>=5.2,<5.3` in Phase 2 (this phase did not modify
dependency files per the planning-only restriction).
**Consequences:** Must be fixed before `pip install -r requirements.txt`.

## ADR-011 — Human-readable booking reference

**Context:** Support staff and patients need a shareable identifier.
**Decision:** `Appointment.reference` (unique, e.g. `CC-2026-000123`) alongside the PK.
**Consequences:** URLs/support can use the reference; the PK stays internal.

## ADR-012 — Public registration = Patient only

**Context:** RBAC requirement.
**Decision:** Registration form hard-codes `role=PATIENT`; staff accounts created only by
Admin (protected flow or management command).
**Consequences:** No self-service privilege escalation; tests must prove `role` from input
is ignored.

---

## Open issues requiring employer confirmation

1. Instant confirmation vs receptionist approval (Q1) — provisional: `REQUESTED` then confirm.
2. Cancellation window (Q3) — provisional: 24 hours.
3. Availability rules and slot length (Q4/Q11) — provisional: weekly recurring, 30 min.
4. Deployment target (Q5) and submission format/deadline (Q6).
5. Whether MySQL is available in the review environment (ADR-003).

## Known repository hygiene issues (found in Phase 1 inspection)

- `README.md` previously contained committed merge-conflict markers; resolved during Phase 1
  documentation update.
- `requirements.txt` Django pin mismatch — tracked as ADR-010 (fix in Phase 2).
