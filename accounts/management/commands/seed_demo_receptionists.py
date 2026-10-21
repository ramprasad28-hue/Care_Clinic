"""Create the two synthetic demo receptionist accounts.

Demo accounts are **not** real staff provisioning: they get unusable
passwords and the reserved ``careclinic.example`` addresses, so nobody can
log in with them until an authorized administrator sets a local password
(``manage.py changepassword <email>`` — sets it in that environment only).

Idempotent: reruns are no-ops. Existing usable passwords are never reset. A
reserved email already held by an account with a different role aborts the
command with a clear error instead of silently re-rolling that user.

    python manage.py seed_demo_receptionists
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

User = get_user_model()

RECEPTIONISTS = [
    {
        "email": "ramprasad.reception@careclinic.example",
        "first_name": "Ramprasad",
        "last_name": "",
    },
    {
        "email": "rishabh.reception@careclinic.example",
        "first_name": "Rishabh",
        "last_name": "",
    },
]


class Command(BaseCommand):
    help = "Create synthetic demo RECEPTIONIST accounts (unusable passwords)."

    @transaction.atomic
    def handle(self, *args, **options):
        for person in RECEPTIONISTS:
            clash = User.objects.filter(email=person["email"]).exclude(
                role=User.Role.RECEPTIONIST
            )
            if clash.exists():
                raise CommandError(
                    f"Refusing to seed receptionist email '{person['email']}': "
                    f"it already belongs to an account with role "
                    f"'{clash.first().role}'. Resolve the conflict manually "
                    "(no records were changed)."
                )

        created_count = 0
        for person in RECEPTIONISTS:
            user, created = User.objects.get_or_create(
                email=person["email"],
                defaults={
                    "first_name": person["first_name"],
                    "last_name": person["last_name"],
                    "role": User.Role.RECEPTIONIST,
                    "is_staff": False,
                    "is_superuser": False,
                },
            )
            if created:
                # Unusable password: no hardcoded secret anywhere in the repo.
                user.set_unusable_password()
                user.is_staff = False
                user.is_superuser = False
                user.save(update_fields=["password", "is_staff", "is_superuser"])
                created_count += 1
            self.stdout.write(
                f"  {person['email']}: "
                f"{'created' if created else 'exists (password untouched)'}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo receptionists ready: {created_count} created, "
                f"{len(RECEPTIONISTS)} total. Log-in requires an authorized "
                "administrator to set a local password (manage.py "
                "changepassword). Run 'sync_roles' to grant receptionist permissions."
            )
        )
