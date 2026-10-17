"""Materialize bookable slots for doctors.

    python manage.py generate_slots                 # every accepting doctor, next 30 days
    python manage.py generate_slots --days 14
    python manage.py generate_slots --doctor <email>
    python manage.py generate_slots --start 2026-01-01 --end 2026-01-31
    python manage.py generate_slots --include-past   # for tests/backfill only

Idempotent: existing slots (including BOOKED ones) are never modified or deleted.
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from clinic.models import Doctor

from appointments.slot_generation import DEFAULT_HORIZON_DAYS, generate_slots

User = get_user_model()


def _parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise CommandError(f"Invalid date '{value}'. Use YYYY-MM-DD.")


class Command(BaseCommand):
    help = "Generate appointment slots from active availability rules."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=DEFAULT_HORIZON_DAYS)
        parser.add_argument("--start", type=str, default=None)
        parser.add_argument("--end", type=str, default=None)
        parser.add_argument(
            "--doctor",
            type=str,
            default=None,
            help="Limit to a single doctor by user email.",
        )
        parser.add_argument(
            "--include-past",
            action="store_true",
            help="Also create slots that have already started (backfill/tests).",
        )

    def handle(self, *args, **options):
        start_date = _parse_date(options["start"]) if options["start"] else None
        end_date = _parse_date(options["end"]) if options["end"] else None

        doctors = None
        if options["doctor"]:
            user = User.objects.filter(email=options["doctor"]).first()
            if user is None or not hasattr(user, "doctor"):
                raise CommandError(f"No doctor found for email '{options['doctor']}'.")
            doctors = Doctor.objects.filter(pk=user.doctor.pk)

        summary = generate_slots(
            start_date=start_date,
            end_date=end_date,
            horizon_days=options["days"],
            doctors=doctors,
            include_past=options["include_past"],
        )
        total = sum(item["created"] for item in summary.values())
        self.stdout.write(
            self.style.SUCCESS(
                f"Generated {total} new slot(s) across {len(summary)} doctor(s)."
            )
        )
