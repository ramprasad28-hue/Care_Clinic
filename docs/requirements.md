# Requirements — Care_Clinic

**Project:** Care_Clinic — Clinic Appointment Management System
**Client:** Anmaya Health Technologies Private Limited (recruitment task)
**Phase:** 1 — Requirements (planning only; no application code)
**Status:** Draft for approval

---

## 1. Confirmed requirements (employer-explicit)

1. **Appointment booking.**
2. **Role-Based Access Control (RBAC).**
3. **Other necessary features for a clinic web application** (professional judgment invited).

Only the three items above are employer-confirmed. Everything else in this document is
**proposed** and must be validated before or during implementation.

## 2. Proposed roles

| Role | Created by | Primary job |
|---|---|---|
| **Patient** | Self-registration | Discover doctors/specialities; book, cancel, reschedule own appointments |
| **Doctor** | Admin | View own schedule; manage availability and leave; update appointment status |
| **Receptionist** | Admin | Book / cancel / reschedule on behalf of patients; check-in; day operations |
| **Admin** | Admin (superuser) | Manage doctors, specialities, users, system configuration |

**Hard rule:** public registration creates **Patient accounts only**. Doctor, Receptionist
and Admin roles must never be obtainable through any public form.

## 3. Proposed features (essential for v1)

### 3.1 Public website (anonymous)
- Home page with clinic introduction and a prominent **Book Appointment** call to action.
- **Speciality** listing and detail page (description + doctors in that speciality).
- **Doctor** listing (filter by speciality) and doctor profile page (qualifications, bio,
  speciality, availability summary) with a Book CTA.
- Contact page (address, phone, email, hours), FAQ, About page.
- Login / logout / password reset / **patient** registration.

### 3.2 Booking (core)
- Select speciality → doctor → date → **available slot** → confirm.
- Server-side availability validation (no client-side trust).
- Booking reference + status shown after success.
- Cancel and reschedule subject to a cancellation window.
- Prevent: past dates, unavailable slots, conflicts, and concurrent double booking.

### 3.3 Dashboards
- **Patient:** own appointments (upcoming/past), book/reschedule/cancel, profile.
- **Doctor:** today's schedule, appointment details, status updates, availability + leave.
- **Receptionist:** day view, book-on-behalf, check-in, confirm/cancel/reschedule.
- **Admin:** manage doctors, specialities, users; appointment oversight; simple metrics.

### 3.4 Administration & data
- CRUD for specialities and doctors (Admin).
- Doctor availability rules and leave dates.
- Appointment status workflow (see `architecture.md` §6).
- Auditable fields (created/updated timestamps and actor where relevant).

### 3.5 Quality
- Server-side form validation on every input.
- Automated tests for RBAC, booking integrity, and validation.
- README + architecture/data-model documentation (this `docs/` set).
- Secure configuration (no secrets committed).

## 4. Out of scope for v1 (explicitly deferred)

Payments/invoicing, prescriptions, medical records/EMR, lab results, insurance claims,
multi-branch/multi-clinic, SMS/email provider integration, native mobile apps, and any
SPA/React/Next.js front end. These are unrequested modules and must not creep into v1.

## 5. Optional future enhancements (post-v1)

- Email/SMS reminders behind a provider-agnostic notification interface.
- Waitlist with automatic fill on cancellation.
- Doctor leave/blackout calendars with recurring weekly templates.
- Calendar export (.ics), reviews, health packages, Tamil/English localization.
- Audit-log UI and richer admin analytics.

## 6. Inspiration from reference sites (verified vs assumption)

All five reference sites were reachable. Verified patterns used for **information
architecture only** (no branding, logos, text, or images are copied):

- Persistent top nav: Home, About, Specialities/Departments, Doctors, Contact.
- Prominent "Book Appointment" CTA (references use phone/WhatsApp; Care_Clinic uses a
  real in-app booking flow).
- Speciality grid → detail pages; doctor grid → profile pages.
- Hero with trust stats; contact block; FAQ; legal footer.

Assumption: none of the references were inspected beyond their rendered home pages, so
deep page structures are unknown and are not treated as requirements.

## 7. Unanswered employer questions and provisional assumptions

| # | Question | Provisional assumption (to confirm) |
|---|---|---|
| Q1 | Instant confirmation vs receptionist approval? | Booking created as `REQUESTED`; receptionist/doctor confirms. Configurable. |
| Q2 | Is MySQL mandatory? | Yes — MySQL with InnoDB (employer stack in Phase 1 brief). |
| Q3 | Cancellation window? | Free self-cancel up to **24 h** before start; later requires staff. |
| Q4 | Doctor availability rules? | Weekly recurring slots; configurable slot length (default 30 min); leave dates block slots. |
| Q5 | Deployment platform? | Generic WSGI (Gunicorn + Nginx); not container-mandatory. |
| Q6 | Submission format & deadline? | Git repo + README + short demo; deadline unknown — plan conservatively. |
| Q7 | Login identity? | Username **or** email; unique email required. |
| Q8 | Patient self-registration allowed? | Yes, Patient role only. |
| Q9 | Timezone / language? | `Asia/Kolkata`, English UI. |
| Q10 | Required branding/design? | Original professional healthcare design; no employer brand assets provided. |
| Q11 | Appointment slot length per speciality? | Default 30 minutes, configurable per doctor. |
| Q12 | Can a patient book multiple doctors per day? | Yes, unless the same doctor/slot (blocked by uniqueness). |

## 8. Acceptance criteria (v1)

1. A Patient can register, book an available slot, view the booking reference, and cancel/reschedule within policy.
2. Two concurrent requests for the same slot cannot both succeed (verified by a concurrency test).
3. A Patient cannot view or modify another Patient's appointment (IDOR blocked on the backend).
4. A Doctor sees only appointments belonging to their own schedule.
5. A Receptionist can book on behalf of a patient and perform permitted operational actions, but cannot manage users.
6. An Admin can manage doctors, specialities, and users.
7. No role other than Admin can reach user/role management endpoints.
8. Past dates, unavailable slots, and conflicts are rejected server-side with clear messages.
