"""Admin configuration for the custom user model."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import Http404
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """UserAdmin adapted for email-based login with privilege-escalation guards.

    Security boundaries for non-superuser ADMINs:
    - User-add is permission-gated on ``accounts.add_user`` (not on staff status).
    - is_superuser / is_staff / role / groups / user_permissions cannot be
      changed by a non-superuser, even through a forged POST: persisted
      values are re-asserted server-side around the save.
    - On delegated (non-superuser) add, is_staff/is_superuser are forced off
      and the Administrator role is not provisionable.
    - Superuser accounts are hidden from non-superuser changelists.
    - Superusers retain full management capability.
    """

    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", "first_name", "last_name", "phone")

    # Fieldsets: keep original Django layout but we control fields via
    # formfield_for_dbfield and permission methods below.
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "phone")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "role",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )

    # ------------------------------------------------------------------
    # QUERYSET: hide superusers from non-superuser admins
    # ------------------------------------------------------------------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(is_superuser=False)
        return qs

    # ------------------------------------------------------------------
    # FORMFIELDS: disable privileged fields for non-superuser admins.
    #            Disabled fields are a UX affordance only — the authoritative
    #            server-side enforcement lives in save_model()/save_related().
    # ------------------------------------------------------------------
    def _is_add_view(self, request):
        match = getattr(request, "resolver_match", None)
        return bool(match) and match.url_name == (
            f"{self.opts.app_label}_{self.opts.model_name}_add"
        )

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name in ("is_staff", "is_superuser", "groups", "user_permissions"):
                kwargs["disabled"] = True
            if db_field.name == "role":
                if self._is_add_view(request):
                    # Delegated provisioning may not select the Administrator
                    # role — restrict the rendered choices instead of silently
                    # downgrading the save.
                    kwargs["choices"] = [
                        choice
                        for choice in db_field.get_choices(include_blank=False)
                        if choice[0] != User.Role.ADMIN
                    ]
                else:
                    kwargs["disabled"] = True
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def get_changeform_initial_data(self, request):
        """Make the disabled add-form flags validate for delegated admins.

        Disabled boolean fields validate against the form's initial dict; on
        the add view a non-superuser must be able to submit the form, so an
        explicit False initial is supplied (save_model forces them anyway).
        """
        initial = super().get_changeform_initial_data(request)
        if not request.user.is_superuser and self._is_add_view(request):
            initial.setdefault("is_staff", False)
            initial.setdefault("is_superuser", False)
        return initial

    # ------------------------------------------------------------------
    # PERMISSIONS: server-side enforcement
    # ------------------------------------------------------------------
    def has_add_permission(self, request):
        """User creation is permission-gated (Option A, ADR-012).

        Policy: superusers always may add; non-superusers may add only when
        they hold the ``accounts.add_user`` model permission (the
        "Administrator" role group is granted it by ``sync_roles``). Staff
        status alone is never a grant. A denied request raises
        PermissionDenied inside Django's changeform handler before any row
        is created.
        """
        return request.user.is_superuser or request.user.has_perm("accounts.add_user")

    def has_change_permission(self, request, obj=None):
        # Allow the change view to run for all eligible users;
        # security for superuser editing is enforced in change_view via Http404.
        if not request.user.is_superuser and obj is not None and obj.is_superuser:
            # Permit the change view to render; our change_view will raise Http404
            return True
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Non-superusers cannot delete superuser accounts
        if obj is not None and obj.is_superuser and not request.user.is_superuser:
            return False
        # Non-superusers cannot delete themselves
        if obj is not None and obj == request.user and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    # ------------------------------------------------------------------
    # SAVE: server-side enforcement of protected values.
    #      A malicious POST is never assumed safe because a field is disabled
    #      in the rendered HTML. For non-superuser change requests the
    #      persisted role/is_staff/is_superuser are read back from the DB and
    #      re-asserted on the instance before it is saved, and the persisted
    #      groups/user_permissions relations are snapshotted and re-applied
    #      after Django's M2M save phase — forged form values can therefore
    #      never overwrite them, and existing rows/relations are never
    #      erased. On delegated add, staff/superuser flags are forced off.
    # ------------------------------------------------------------------
    def _protected_snapshot(self, request, obj):
        """Persisted protected values for ``obj`` read fresh from the DB."""
        trusted = User.objects.filter(pk=obj.pk)
        row = trusted.values("role", "is_staff", "is_superuser").first()
        if row is None:
            return None
        fresh = trusted.get()
        return {
            "role": row["role"],
            "is_staff": row["is_staff"],
            "is_superuser": row["is_superuser"],
            "groups": [pk for pk, in fresh.groups.values_list("pk")],
            "user_permissions": [pk for pk, in fresh.user_permissions.values_list("pk")],
        }

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            if change:
                snapshot = self._protected_snapshot(request, obj)
                if snapshot is None:
                    raise Http404("User not found")
                obj.role = snapshot["role"]
                obj.is_staff = snapshot["is_staff"]
                obj.is_superuser = snapshot["is_superuser"]
            else:
                obj.is_staff = False
                obj.is_superuser = False
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        reclaim = None
        if not request.user.is_superuser and change:
            # Snapshot BEFORE Django saves the (post-)form M2M values.
            reclaim = self._protected_snapshot(request, form.instance)
        super().save_related(request, form, formsets, change)
        if reclaim is not None:
            form.instance.groups.set(reclaim["groups"])
            form.instance.user_permissions.set(reclaim["user_permissions"])

    # ------------------------------------------------------------------
    # CHANGE VIEW: block non-superusers from editing superuser accounts
    #             with a 404 not found response (preserves UX consistency)
    #             and prevents any sensitive account details from being exposed.
    # ------------------------------------------------------------------
    def change_view(self, request, object_id, form_url='', extra_context=None):
        obj = self.get_object(request, object_id)
        # Raise 404 if a non-superuser attempts to access a superuser edit page.
        # This hides the existence of superuser accounts from non-administrators
        # while still denying access, without revealing permission-details.
        if obj is not None and obj.is_superuser and not request.user.is_superuser:
            raise Http404("Superuser account")
        return super().change_view(request, object_id, form_url, extra_context)