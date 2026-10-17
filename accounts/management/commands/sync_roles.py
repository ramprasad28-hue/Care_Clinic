"""Synchronise role groups and their permissions.

Creates one Django ``Group`` per role and grants a configurable set of
permissions to each. As domain apps (clinic, appointments, ...) are added in
later phases, extend ``ROLE_PERMISSIONS`` below; permissions that do not exist
yet are skipped safely, so this command is idempotent and forward-compatible.

It also reconciles group membership with each user's ``role`` field: every user
is added to the group matching their role (GOD-mode superusers/administrators
keep their existing groups).

    python manage.py sync_roles
    python manage.py sync_roles --dry-run
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()

# Role -> (group name, permissions as "app_label.codename").
# Only entries whose Permission exists are applied. Keep this list aligned with
# the RBAC matrix in docs/architecture.md §6 as features land.
ROLE_PERMISSIONS = {
    User.Role.PATIENT: (
        "Patient",
        [
            "clinic.view_speciality",
            "clinic.view_doctor",
            "appointments.add_appointment",
            "appointments.view_appointment",
        ],
    ),
    User.Role.DOCTOR: (
        "Doctor",
        [
            "clinic.view_speciality",
            "clinic.view_doctor",
            "clinic.add_availabilityrule",
            "clinic.change_availabilityrule",
            "clinic.delete_availabilityrule",
            "clinic.view_availabilityrule",
            "clinic.add_doctorleave",
            "clinic.change_doctorleave",
            "clinic.delete_doctorleave",
            "clinic.view_doctorleave",
            "appointments.view_appointment",
            "appointments.change_appointment",
            "appointments.view_appointmentslot",
        ],
    ),
    User.Role.RECEPTIONIST: (
        "Receptionist",
        [
            "clinic.view_speciality",
            "clinic.view_doctor",
            "appointments.view_appointment",
            "appointments.add_appointment",
            "appointments.change_appointment",
            "appointments.view_appointmentslot",
            "appointments.add_appointmentslot",
            "appointments.change_appointmentslot",
        ],
    ),
    User.Role.ADMIN: (
        "Administrator",
        [
            "accounts.add_user",
            "accounts.change_user",
            "accounts.delete_user",
            "accounts.view_user",
            "clinic.add_speciality",
            "clinic.change_speciality",
            "clinic.delete_speciality",
            "clinic.view_speciality",
            "clinic.add_doctor",
            "clinic.change_doctor",
            "clinic.delete_doctor",
            "clinic.view_doctor",
            "clinic.add_availabilityrule",
            "clinic.change_availabilityrule",
            "clinic.delete_availabilityrule",
            "clinic.view_availabilityrule",
            "clinic.add_doctorleave",
            "clinic.change_doctorleave",
            "clinic.delete_doctorleave",
            "clinic.view_doctorleave",
            "appointments.add_appointment",
            "appointments.change_appointment",
            "appointments.delete_appointment",
            "appointments.view_appointment",
            "appointments.add_appointmentslot",
            "appointments.change_appointmentslot",
            "appointments.delete_appointmentslot",
            "appointments.view_appointmentslot",
        ],
    ),
}


class Command(BaseCommand):
    help = "Create role groups, sync permissions, and reconcile group membership."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report the changes that would be made without applying them.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        groups = {}
        created_count = 0
        perm_total = 0
        missing = []

        for role, (group_name, codenames) in ROLE_PERMISSIONS.items():
            if dry_run:
                group = Group.objects.filter(name=group_name).first()
                outcome = "exists" if group else "would create"
            else:
                group, created = Group.objects.get_or_create(name=group_name)
                if created:
                    created_count += 1
                outcome = "created" if created else "exists"
            self.stdout.write(f"  group '{group_name}' ({role}): {outcome}")

            perms = []
            for ref in codenames:
                app_label, codename = ref.split(".", 1)
                perm = Permission.objects.filter(
                    content_type__app_label=app_label, codename=codename
                ).first()
                if perm is None:
                    missing.append(ref)
                    continue
                perms.append(perm)

            if not dry_run and perms:
                group.permissions.set(perms)
            perm_total += len(perms)
            groups[role] = group

        if dry_run:
            member_count = User.objects.count()
        else:
            member_count = 0
            for user in User.objects.all():
                entry = groups.get(user.role)
                if entry is not None:
                    user.groups.add(entry)
                    member_count += 1

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}Roles synced: {created_count} group(s) created, "
                f"{perm_total} permission(s) granted, "
                f"{member_count} user(s) reconciled."
            )
        )
        if missing:
            self.stdout.write(
                self.style.WARNING(
                    "Skipped permissions not yet defined: " + ", ".join(sorted(missing))
                )
            )
