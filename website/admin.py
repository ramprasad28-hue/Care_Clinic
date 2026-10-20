"""Django admin for the website imagery registry (ADR-022, phase C1).

``WebsiteSectionImage`` is administrator-only, exactly like the clinic's
business-asset models (the ``AdministratorOnlyMixin`` rules are reused; any
staff member who is not an administrator sees no module). Previews and
post-save dimension warnings follow the same hand-rolled pattern as the
clinic admins — no new admin dependencies.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from clinic.admin import (
    AdministratorOnlyMixin,
    ImageWarningAdminMixin,
    _media_src,
)

from .forms import WebsiteSectionImageAdminForm
from .models import WebsiteSectionImage


@admin.register(WebsiteSectionImage)
class WebsiteSectionImageAdmin(ImageWarningAdminMixin, AdministratorOnlyMixin, admin.ModelAdmin):
    form = WebsiteSectionImageAdminForm
    list_display = ("key", "name", "image_thumb", "is_active", "updated_at")
    list_filter = ("key", "is_active")
    search_fields = ("key", "name")
    ordering = ("key",)
    readonly_fields = ("image_preview",)
    fieldsets = (
        (None, {"fields": ("key", "name")}),
        (
            _("Image"),
            {"fields": ("image_preview", "image", "alt_text", "caption", "is_active")},
        ),
    )

    def image_thumb(self, obj):
        src = _media_src(obj.image)
        if not src:
            return "—"
        return format_html('<img src="{}" style="max-height:52px;border-radius:4px" alt="">', src)
    image_thumb.short_description = _("Image")

    @admin.display(description=_("Current image"))
    def image_preview(self, obj):
        src = _media_src(obj.image)
        if not src:
            return _("No image uploaded — the section keeps its documented static fallback.")
        return format_html(
            '<img src="{}" style="max-height:140px;border-radius:6px" alt="">', src
        )
