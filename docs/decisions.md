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
**Status (Phase 2):** `mysqlclient 2.3.0` installed successfully via a **prebuilt
`cp312-win_amd64` wheel** — no C toolchain required, so no fallback needed. MySQL Server 8.0
is installed and running on port 3306, but **no credentials were available** to this session,
so the SQLite fallback was used for framework checks/tests. **MySQL migration validation
remains BLOCKED** until credentials and the `care_clinic` database are provisioned.
**Consequences:** Tests currently run against SQLite (documented). Re-run `migrate` and the
suite against MySQL before delivery to satisfy this ADR.

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

## ADR-010 — `requirements.txt` alignment (RESOLVED in Phase 2)

**Context:** Current pin `Django>=5.0,<5.2` conflicts with the mandated Django 5.2 LTS.
**Decision:** Update to `Django>=5.2,<5.3` in Phase 2.
**Status:** ✅ Resolved — `requirements.txt` now pins `Django>=5.2,<5.3`; **Django 5.2.18**
installed and verified in the virtual environment.
**Consequences:** No action remaining.

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

## ADR-013 — `Doctor.speciality` is a single foreign key (Phase 4)

**Context:** `docs/data-model.md` models a doctor as belonging to one speciality; the
brief speaks of "Dr. Aswin — Cardiology, Dermatology" as an example, which could imply
many-to-many.
**Decision:** Keep a **single `ForeignKey(Speciality, on_delete=PROTECT)`**, matching the
approved data model. A doctor has exactly one speciality.
**Consequences:** Simpler filtering, admin, and public pages; speciality lists are cheap
(`speciality.doctors`). If multi-speciality doctors are later required, migrate to an
explicit through-model — deferred until requested (YAGNI). `PROTECT` prevents deleting a
speciality that still has doctors.

## ADR-014 — Justified additions to `Doctor`: `slug` and `consultation_fee` (Phase 4)

**Context:** The data model lists the doctor's core fields; the public listing needs stable,
readable URLs and the appointment flow will need a fee.
**Decision:** Add `slug` (unique, auto-generated from the doctor's name via `unique_slug()`)
and `consultation_fee` (`Decimal`, nullable — not all clinics charge per-consultation).
**Consequences:** Public doctor URLs are human-readable (`/doctors/aswin-kumar/`) instead of
pks. `consultation_fee` is optional so it can remain blank. Both are additive and do not
contradict the model.

## ADR-015 — Deliberately omit `Doctor.profile_image` in v1 (Phase 4)

**Context:** A profile photo was considered for doctor pages.
**Decision:** **Omit** `profile_image` for v1.
**Consequences:** No image-handling pipeline and, importantly, **no Pillow dependency**,
keeping the dependency set minimal and the reviewer setup simple. The UI uses a text/initial
avatar. Revisit only if the employer requests photos.


## ADR-016 — Materialize concrete `AppointmentSlot` rows (Phase 5)

**Context:** Availability is stored as recurring weekly `AvailabilityRule` windows. Booking
needs a definite, lockable row that can be uniquely claimed and that leave/past filtering has
already been applied to.
**Decision:** Generate concrete `AppointmentSlot` rows from active rules via the reusable
`slot_generation` service and the idempotent `python manage.py generate_slots` command
(rolling horizon, default 30 days). Slots are never recomputed on the fly at booking time.
**Consequences:** `SELECT ... FOR UPDATE` has a real row to lock; the
`UniqueConstraint(doctor, date, start_time)` prevents duplicate materialization; re-running
the command is safe and preserves `BOOKED` slots; `DoctorLeave` and past intervals are excluded
at generation. Slots are disposable scheduling artifacts (deleting a doctor cascades), whereas
appointments are protected history.

## ADR-017 — One active booking per slot via a nullable `OneToOneField` + release-on-cancel

**Context:** The data model proposed a *conditional* unique constraint (unique on `slot` only
when the appointment is active). Django silently **skips** conditional unique constraints on
backends without partial-index support — verified for MySQL (`_unique_supported` requires
`supports_partial_indexes`), so that guarantee would not exist in production.
**Decision:** Model `Appointment.slot` as a **nullable `OneToOneField`**. Cancelling or
rescheduling detaches the slot (`slot = NULL`) and returns it to `OPEN`. The plain underlying
unique index therefore only ever covers the single *active* appointment for a slot.
**Consequences:** A **hard, portable** database guarantee of at most one active booking per
slot on MySQL, SQLite, and PostgreSQL — no reliance on unsupported conditional indexes.
Appointment history is preserved (row + date/time snapshots + cancellation metadata), and the
released slot can be rebooked. Concurrency is additionally serialized by `select_for_update()`
on MySQL/InnoDB.

## ADR-018 — Appointment status state machine + 24-hour self-service window

**Context:** Bookings move through several states (request → confirm → check-in → complete,
plus cancel / no-show). The brief did not fix the confirmation model or a cancellation window.
**Decision:** Enforce an explicit `ALLOWED_TRANSITIONS` state machine; terminal states
(`COMPLETED`, `CANCELLED`, `NO_SHOW`) admit no further transitions. Cancellation is always a
dedicated flow (never a raw status change). Patients may freely cancel/reschedule only up to
`CANCELLATION_WINDOW = 24h` before the slot; staff may do so at any time until the slot starts.
**Consequences:** Illegal transitions are rejected server-side with user-facing errors; the
UI hides actions the user may not take. The 24h window is **provisional** pending employer
confirmation (open issue Q3) and is defined in one constant to make a later change trivial.

## ADR-019 — Dashboards are thin, read-mostly views over existing services (Phase 6)

**Context:** Phase 6 needs four role-specific dashboards (Patient, Doctor, Receptionist,
Admin) with search/filtering and a few new actions (status changes, book-on-behalf). The
existing `appointments` app already owns all booking state and its transactional services and
scoped querysets.
**Decision:** Add a new `dashboards` app that contains **no models and no migrations**. Its
views compose existing data: reads go through `Appointment.objects.for_user` (ownership first,
then optional filtering/pagination in `dashboards/selectors.py`); writes delegate to
`appointments.services` (`book_slot`, `transition_status`). A single landing route
(`/dashboard/`) redirects each authenticated user to their role's dashboard by reading the
role from the session — never from the request body — and renders a safe page for an
unrecognised role.
**Consequences:** No schema churn and a single source of truth for booking rules and IDOR
scoping; dashboards stay presentational and cheap to test. `LOGIN_REDIRECT_URL` is left as
`/` so the existing login-redirect test is preserved; users reach `/dashboard/` via the nav
link. Book-on-behalf validates the submitted patient/doctor id through `ModelChoiceField`s
before calling the service, so a forged id cannot be used.

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
