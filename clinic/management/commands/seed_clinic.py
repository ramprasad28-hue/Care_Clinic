"""Seed the clinic catalog with synthetic development data.

Creates a handful of specialities, DOCTOR-role users with linked doctor
profiles, weekly availability rules, and a sample leave block. All data is
**synthetic** — no real patient or clinician information is used.

Idempotent: safe to run multiple times (uses ``get_or_create`` /
``update_or_create``). Safe to run in any environment.

    python manage.py seed_clinic
"""
from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from clinic.models import AvailabilityRule, Doctor, DoctorLeave, Speciality, Weekday

User = get_user_model()

SPECIALITIES = [
    ("Cardiology", "Heart and cardiovascular care, diagnostics, and follow-up."),
    ("Dermatology", "Skin, hair, and nail conditions for all ages."),
    ("General Medicine", "Primary care, preventive checks, and common illnesses."),
    ("Paediatrics", "Healthcare for infants, children, and adolescents."),
    ("Orthopaedics", "Bones, joints, and musculoskeletal injury care."),
]

DOCTORS = [
    {
        "email": "dr.aswin@careclinic.example",
        "first_name": "Aswin",
        "last_name": "Kumar",
        "speciality": "Cardiology",
        "registration_number": "MCI-CARD-1001",
        "qualification": "MBBS, MD (Cardiology)",
        "bio": "Consultant cardiologist focused on preventive heart care.",
        "consultation_fee": "600.00",
    },
    {
        "email": "dr.meera@careclinic.example",
        "first_name": "Meera",
        "last_name": "Nair",
        "speciality": "Dermatology",
        "registration_number": "MCI-DERM-1002",
        "qualification": "MBBS, MD (Dermatology)",
        "bio": "Dermatologist treating clinical and cosmetic skin concerns.",
        "consultation_fee": "450.00",
    },
    {
        "email": "dr.rahul@careclinic.example",
        "first_name": "Rahul",
        "last_name": "Verma",
        "speciality": "General Medicine",
        "registration_number": "MCI-GEN-1003",
        "qualification": "MBBS",
        "bio": "General physician providing primary and preventive care.",
        "consultation_fee": "300.00",
    },
]

# (weekday, start, end, slot_length) windows applied to every seeded doctor.
WEEKDAY_WINDOWS = [
    (Weekday.MONDAY, time(9, 0), time(13, 0), 15),
    (Weekday.MONDAY, time(15, 0), time(18, 0), 15),
    (Weekday.WEDNESDAY, time(9, 0), time(13, 0), 15),
    (Weekday.FRIDAY, time(9, 0), time(13, 0), 15),
]


class Command(BaseCommand):
    help = "Create synthetic specialities, doctors, availability, and leave."

    @transaction.atomic
    def handle(self, *args, **options):
        specialities = {}
        for name, description in SPECIALITIES:
            obj, created = Speciality.objects.update_or_create(
                name=name,
                defaults={"description": description, "is_active": True},
            )
            specialities[name] = obj
            self.stdout.write(f"  speciality '{name}': {'created' if created else 'exists'}")

        for spec in DOCTORS:
            user, u_created = User.objects.get_or_create(
                email=spec["email"],
                defaults={
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "role": User.Role.DOCTOR,
                },
            )
            if not u_created:
                user.first_name = spec["first_name"]
                user.last_name = spec["last_name"]
                user.role = User.Role.DOCTOR
                user.save(update_fields=["first_name", "last_name", "role"])
            else:
                user.set_unusable_password()
                user.save(update_fields=["password"])

            doctor, d_created = Doctor.objects.update_or_create(
                user=user,
                defaults={
                    "speciality": specialities[spec["speciality"]],
                    "registration_number": spec["registration_number"],
                    "qualification": spec["qualification"],
                    "bio": spec["bio"],
                    "consultation_fee": spec["consultation_fee"],
                    "is_accepting_appointments": True,
                },
            )
            self.stdout.write(
                f"  doctor '{spec['email']}': {'created' if d_created else 'exists'}"
            )

            for weekday, start, end, slot in WEEKDAY_WINDOWS:
                AvailabilityRule.objects.get_or_create(
                    doctor=doctor,
                    weekday=weekday,
                    start_time=start,
                    end_time=end,
                    defaults={"slot_length_minutes": slot, "is_active": True},
                )

            leave_start = date.today() + timedelta(days=30)
            DoctorLeave.objects.get_or_create(
                doctor=doctor,
                start_date=leave_start,
                end_date=leave_start + timedelta(days=1),
                defaults={"reason": "Synthetic sample leave"},
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(specialities)} specialities and {len(DOCTORS)} doctors "
                "(synthetic data)."
            )
        )
