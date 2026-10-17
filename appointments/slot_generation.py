"""Reusable slot-generation service.

Materializes concrete :class:`~appointments.models.AppointmentSlot` rows from
``clinic.AvailabilityRule`` windows for a rolling date range.

Guarantees (see Task 2 of the Phase 5 brief):

* Uses the configured timezone (``settings.TIME_ZONE`` = ``Asia/Kolkata``) so
  "past" is evaluated correctly.
* Respects each rule's ``weekday``, ``start_time``, ``end_time`` and
  ``effective_slot_length_minutes`` (rule override, else doctor default).
* Never emits a slot that extends past the rule's end time.
* Excludes dates covered by ``clinic.DoctorLeave``.
* Excludes slots that have already started (past intervals) by default.
* Is idempotent: re-running never creates duplicate slots (unique constraint +
  an explicit existence check); existing rows — including ``BOOKED`` ones — are
  left untouched and never deleted.
* Degrades safely with overlapping/invalid rules: invalid windows are ignored
  and overlapping candidate intervals are de-duplicated.

This logic lives entirely outside the views.
"""
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from django.db import IntegrityError
from django.utils import timezone

from clinic.models import AvailabilityRule, Doctor, DoctorLeave

from .models import AppointmentSlot

DEFAULT_HORIZON_DAYS = 30


def _aware(day, time_value):
    return timezone.make_aware(
        datetime.combine(day, time_value), timezone.get_current_timezone()
    )


def _rule_intervals(rule, day):
    """Yield ``(start_time, end_time)`` intervals for one rule on one day.

    Returns nothing for an invalid window (end <= start or non-positive length).
    """
    length = rule.effective_slot_length_minutes
    if not length or length <= 0:
        return
    if not rule.start_time or not rule.end_time or rule.end_time <= rule.start_time:
        return
    step = timedelta(minutes=length)
    cursor = datetime.combine(day, rule.start_time)
    limit = datetime.combine(day, rule.end_time)
    while cursor + step <= limit:
        yield cursor.time(), (cursor + step).time()
        cursor += step


def _non_overlapping(intervals):
    """Drop candidates that overlap an already-accepted interval (sorted by start)."""
    accepted = []
    last_end = None
    for start, end in sorted(intervals, key=lambda interval: interval[0]):
        if last_end is not None and start < last_end:
            continue
        accepted.append((start, end))
        last_end = end
    return accepted


def _leave_dates(doctor, start_date, end_date):
    """Set of individual dates on which ``doctor`` is on leave within the range."""
    dates = set()
    leaves = DoctorLeave.objects.filter(
        doctor=doctor, start_date__lte=end_date, end_date__gte=start_date
    ).only("start_date", "end_date")
    for leave in leaves:
        day = max(leave.start_date, start_date)
        last = min(leave.end_date, end_date)
        while day <= last:
            dates.add(day)
            day += timedelta(days=1)
    return dates


def generate_slots_for_doctor(
    doctor,
    start_date,
    end_date,
    *,
    now=None,
    include_past=False,
):
    """Create missing slots for ``doctor`` across ``[start_date, end_date]``.

    Returns a summary dict: ``{"created", "existing", "considered"}``.
    """
    now = now or timezone.now()
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    rules_by_weekday = defaultdict(list)
    rules = (
        AvailabilityRule.objects.filter(doctor=doctor, is_active=True)
        .select_related("doctor")
        .order_by("start_time", "end_time")
    )
    for rule in rules:
        rules_by_weekday[rule.weekday].append(rule)

    leave_dates = _leave_dates(doctor, start_date, end_date)

    candidates = []  # (date, start_time, end_time)
    day = start_date
    while day <= end_date:
        if day not in leave_dates:
            intervals = []
            for rule in rules_by_weekday.get(day.weekday(), []):
                intervals.extend(_rule_intervals(rule, day))
            for start_time, end_time in _non_overlapping(intervals):
                if not include_past and _aware(day, start_time) <= now:
                    continue
                candidates.append((day, start_time, end_time))
        day += timedelta(days=1)

    # De-duplicate candidates within this batch (date, start_time is the key).
    unique = {}
    for day, start_time, end_time in candidates:
        unique.setdefault((day, start_time), end_time)
    candidates = [(d, s, e) for (d, s), e in unique.items()]

    # Skip slots that already exist so existing (possibly BOOKED) rows are kept.
    existing = set(
        AppointmentSlot.objects.filter(
            doctor=doctor, date__range=(start_date, end_date)
        ).values_list("date", "start_time")
    )
    new_slots = [
        AppointmentSlot(
            doctor=doctor,
            date=day,
            start_time=start_time,
            end_time=end_time,
            status="OPEN",
        )
        for day, start_time, end_time in candidates
        if (day, start_time) not in existing
    ]

    created = 0
    if new_slots:
        # ``ignore_conflicts`` is a final race guard; uniqueness is enforced by
        # the UniqueConstraint(doctor, date, start_time) at the database level.
        try:
            AppointmentSlot.objects.bulk_create(new_slots, ignore_conflicts=True)
            created = AppointmentSlot.objects.filter(
                doctor=doctor, date__range=(start_date, end_date)
            ).count() - len(existing)
        except IntegrityError:  # pragma: no cover - defensive
            created = 0

    return {
        "created": created,
        "existing": len(existing),
        "considered": len(candidates),
    }


def generate_slots(
    start_date=None,
    end_date=None,
    *,
    horizon_days=DEFAULT_HORIZON_DAYS,
    doctors=None,
    now=None,
    include_past=False,
):
    """Generate slots for many doctors over a rolling window.

    Defaults to ``today`` .. ``today + horizon_days`` across every doctor with an
    active user and accepting appointments.
    """
    now = now or timezone.now()
    today = timezone.localdate(now)
    start_date = start_date or today
    end_date = end_date or (today + timedelta(days=horizon_days))

    if doctors is None:
        doctors = Doctor.objects.accepting().filter(user__is_active=True)

    summary = {}
    for doctor in doctors:
        summary[doctor.pk] = generate_slots_for_doctor(
            doctor, start_date, end_date, now=now, include_past=include_past
        )
    return summary
