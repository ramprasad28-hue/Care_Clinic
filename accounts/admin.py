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
    - is_superuser / is_staff / groups / user_permissions are hidden/disabled.
    - Role cannot be changed by a non-superuser via the admin UI.
    - Superuser accounts are hidden from non-superuser changelists.
    - Non-superusers cannot create accounts with is_staff=True or is_superuser=True.
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
    # FORMFIELDS: disable privileged fields for non-superuser admins
    #            (server-side enforcement; UI greyed-out + save_model strips)
    # ------------------------------------------------------------------
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "is_staff" and not request.user.is_superuser:
            kwargs["disabled"] = True
        if db_field.name == "is_superuser" and not request.user.is_superuser:
            kwargs["disabled"] = True
        if db_field.name == "groups" and not request.user.is_superuser:
            kwargs["disabled"] = True
        if db_field.name == "user_permissions" and not request.user.is_superuser:
            kwargs["disabled"] = True
        if db_field.name == "role" and not request.user.is_superuser:
            kwargs["disabled"] = True
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    # ------------------------------------------------------------------
    # PERMISSIONS: server-side enforcement
    # ------------------------------------------------------------------
    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True
        # Non-superusers can access the add page but will be restricted
        # by save_model and the disabled form fields.
        return True

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
    # SAVE MODEL: strip privileged flags ONLY if non-superuser explicitly
    #             tries to grant them (preserve current values otherwise,
    #             e.g. disabled fields submit the current value)
    # ------------------------------------------------------------------
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            # Only strip is_staff if the non-superuser is explicitly trying to
            # grant it (form value True and different from current object value)
            if form.cleaned_data.get("is_staff") is True and form.cleaned_data["is_staff"] != obj.is_staff:
                obj.is_staff = False
            # Only strip is_superuser if the non-superuser is explicitly trying
            # to grant it (form value True and different from current object value)
            if form.cleaned_data.get("is_superuser") is True and form.cleaned_data["is_superuser"] != obj.is_superuser:
                obj.is_superuser = False
        super().save_model(request, obj, form, change)

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