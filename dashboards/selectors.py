"""Read helpers shared by the role dashboards.

The dashboards never hand-roll appointment queries. Callers first obtain an
already-authorized queryset (``Appointment.objects.for_user``) and only then
apply the optional scope/search filters below — so ownership is always enforced
*before* filtering, and a foreign reference or invalid filter cannot leak data.
"""
from datetime import datetime

from django.core.paginator import Paginator
from django.utils import timezone

from appointments.models import Appointment, AppointmentStatus

#: Valid appointment statuses (accepted by the ``status`` filter).
VALID_STATUSES = {value for value, _label in AppointmentStatus.choices}

#: Recognised scopes. Anything else falls back to ``upcoming``.
SCOPES = ("upcoming", "today", "past", "all")

DEFAULT_PER_PAGE = 10


def parse_date(value):
    """Parse a ``YYYY-MM-DD`` string, returning ``None`` when malformed."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def apply_scope(queryset, scope):
    """Restrict ``queryset`` to a date scope (defaults safely to ``upcoming``)."""
    today = timezone.localdate()
    if scope == "past":
        return queryset.filter(date__lt=today)
    if scope == "today":
        return queryset.filter(date=today)
    if scope == "all":
        return queryset
    # Unknown/blank scope -> upcoming (the safe default).
    return queryset.filter(date__gte=today)


def filter_appointments(
    queryset,
    *,
    scope=None,
    date=None,
    status=None,
    doctor=None,
    patient=None,
    reference=None,
):
    """Apply validated, optional filters to an already-scoped queryset.

    Every argument is optional and is silently ignored when ``None``/blank, so
    malformed input degrades to "no filter" rather than raising.
    """
    queryset = apply_scope(queryset, scope)
    if date is not None:
        queryset = queryset.filter(date=date)
    if status in VALID_STATUSES:
        queryset = queryset.filter(status=status)
    if doctor is not None:
        queryset = queryset.filter(doctor=doctor)
    if patient is not None:
        queryset = queryset.filter(patient=patient)
    if reference:
        queryset = queryset.filter(reference__icontains=str(reference).strip())
    return queryset


def paginate(queryset, request, per_page=DEFAULT_PER_PAGE):
    """Paginate ``queryset``; invalid/out-of-range pages fall back safely."""
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))


def querystring_without_page(request):
    """Return the current query string minus ``page`` (for pagination links)."""
    params = request.GET.copy()
    params.pop("page", None)
    return params.urlencode()
