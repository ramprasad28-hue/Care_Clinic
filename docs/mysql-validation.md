# MySQL / InnoDB validation procedure — Care_Clinic

The project targets **MySQL 8 with InnoDB** (ADR-003). In the current environment the MySQL
server runs on port 3306, but **no credentials are available** (`ERROR 1045 (28000): Access
denied`), so migrations and the test suite were run against the documented **SQLite fallback**
(`DB_ENGINE=sqlite`). This document records exactly what must be re-run and observed once a
MySQL user is provided. **Do not treat SQLite results as MySQL validation.**

## 1. Configure MySQL

Create the database and a least-privilege user (as a MySQL admin):

```sql
CREATE DATABASE care_clinic CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'care_clinic_user'@'localhost' IDENTIFIED BY '<strong-password>';
GRANT ALL PRIVILEGES ON care_clinic.* TO 'care_clinic_user'@'localhost';
FLUSH PRIVILEGES;
```

In `.env` set `DB_ENGINE=mysql` and the `DATABASE_*` values. Confirm the driver/connection:

```powershell
python manage.py check
python manage.py shell -c "from django.db import connection; print(connection.vendor, connection.get_connection_params()['host'])"
# expect: mysql 127.0.0.1
```

## 2. Migrations

```powershell
python manage.py makemigrations --check --dry-run   # expect: No changes detected
python manage.py migrate                            # expect: all migrations apply, no errors
```

Then confirm InnoDB, the unique index, and the check constraints actually exist on MySQL
(they are the parts Django cannot enforce portably — see ADR-017):

```sql
SHOW TABLE STATUS FROM care_clinic LIKE 'appointments_appointment';         -- Engine: InnoDB
SHOW INDEX FROM care_clinic.appointments_appointment;                       -- unique index on slot_id
SHOW CREATE TABLE care_clinic.appointmentslot;                             -- check + unique constraints
```

Specifically verify:

- `appointments_appointment.slot_id` has a **UNIQUE** index (one active booking per slot).
- `appointments_appointmentslot` has `UNIQUE (doctor_id, date, start_time)`.
- Both tables are **InnoDB** (row-level locking for `SELECT ... FOR UPDATE`).

## 3. Test suite

```powershell
python manage.py test          # full suite
pytest -q                      # same suite via pytest-django
```

On MySQL the previously-skipped test runs instead of skipping:

- `appointments.tests.BookingConcurrencyTests.test_concurrent_booking_has_single_winner`

It spawns two threads that book the **same** slot simultaneously (each with its own DB
connection). Expected: **exactly one** thread succeeds and one is rejected, and
`Appointment.objects.filter(slot=slot).count() == 1`. If both succeed, InnoDB locking is not
in effect (check the table engine and that the connection is not autocommit-bypassed).

Run just that test to iterate quickly:

```powershell
python manage.py test appointments.tests.BookingConcurrencyTests -v 2
```

## 4. Deadline / functional smoke

```powershell
python manage.py migrate
python manage.py sync_roles
python manage.py seed_clinic
python manage.py generate_slots --days 21
python manage.py runserver
```

Then manually: book a slot as a patient, confirm the reference `CC-YYYY-NNNNNN`, cancel it,
and confirm the slot returns to `OPEN` and can be rebooked.

## 5. Acceptance checklist

- [ ] `manage.py migrate` applies cleanly on MySQL; tables are InnoDB.
- [ ] `makemigrations --check --dry-run` reports no changes.
- [ ] Unique index on `Appointment.slot` and `(doctor, date, start_time)` on `AppointmentSlot`
      both exist in MySQL.
- [ ] Full suite green on MySQL, including the concurrency test (**not skipped**).
- [ ] Manual booking/cancel/rebook smoke passes.
