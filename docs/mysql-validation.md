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

## 6. Optional MySQL TLS (`DATABASE_SSL_CA`)

The documented local setup (§1) is **localhost**: `DATABASE_HOST` defaults to
`127.0.0.1`, and the connection options are only `charset=utf8mb4` plus the
strict `init_command`. When `DATABASE_SSL_CA` is unset or empty (or
whitespace-only), the connection behaves exactly as before — nothing changes
locally, and the SQLite fallback never receives any TLS option.

A **remote** MySQL deployment is a different matter: credentials would cross
an untrusted network in plaintext unless the connection is TLS-protected.
If a deployment points `DATABASE_HOST` at a remote server, set
`DATABASE_SSL_CA` in `.env` to a CA certificate bundle that identifies the
server. The project config then adds `ssl: {"ca": <path>}` **and an explicit
`ssl_mode = VERIFY_IDENTITY`** to the MySQL client options: the connection
must be encrypted, the server certificate chain is verified against the
given CA, and the certificate's **hostname** is verified too. `VERIFY_CA`
(and the bare legacy `ssl` dict, which only verifies the chain) are
deliberately not used, and there is no PREFERRED/REQUIRED/skip-verify
fallback for this TLS-enabled configuration.

What still must be configured separately by whoever deploys (not in code):

- MySQL users/grants for the remote host (§1's `'…'@'localhost'` user cannot
  log in remotely).
- Network/firewall access to the MySQL port.
- The CA bundle file itself, plus any server certificate expiry/rotation.
- Mutual TLS (client certificates) is **not** configured by this project;
  add it only if the database host actually requires it.

Confirm the composed client options without connecting:

```powershell
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['OPTIONS'])"
# local:  {'charset': 'utf8mb4', 'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"}
# remote: same dict plus 'ssl': {'ca': <DATABASE_SSL_CA path>}
#              and 'ssl_mode': 'VERIFY_IDENTITY'
```

Note: TLS behavior against a **real remote server** has not been exercised —
no provider/host exists yet. These options are the documented mechanism;
remote deployment testing is part of the hosting decision (see
`docs/decisions.md` open issues).
