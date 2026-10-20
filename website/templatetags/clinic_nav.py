"""Template helpers for shared navigation content (footer, navbar menus)."""
from django import template

from clinic.models import Doctor, Speciality

register = template.Library()


@register.simple_tag
def footer_specialities():
    """Active specialities for the shared footer departments column."""
    return Speciality.objects.active()


@register.simple_tag
def nav_doctors():
    """Public doctors (single query, names/specialities prefetched) for the
    navbar Doctors mega menu. Same visibility rules as the doctor listing."""

    return Doctor.objects.public().select_related("user", "speciality")[:6]
