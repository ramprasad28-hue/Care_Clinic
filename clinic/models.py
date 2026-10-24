"""Clinic domain models: specialities, doctors, availability, and leave.

This app owns the *catalog* and *scheduling configuration* only. Booking
(concrete slots and appointments) is Phase 5 and lives in the ``appointments``
app. The field set follows ``docs/data-model.md`` with two documented,
justified additions to ``Doctor`` (``slug`` and ``consultation_fee``) and one
deliberate omission (``profile_image``) — see ``docs/decisions.md``
ADR-013/ADR-014/ADR-015. ADR-022 (phase C1) supersedes the ADR-015 omission:
``Doctor.profile_image`` and ``Speciality.image`` are administrator-managed
uploads; ``None`` keeps the pre-C1 rendering untouched.

Integrity approach:
* ``CheckConstraint`` enforces time/date ordering at the database level.
* ``UniqueConstraint`` prevents exactly-duplicate availability windows.
* ``Model.full_clean()`` (invoked from ``save()``) adds friendlier, earlier
  validation, including overlap detection and the doctor-role rule.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Weekday(models.IntegerChoices):
    MONDAY = 0, _("Monday")
    TUESDAY = 1, _("Tuesday")
    WEDNESDAY = 2, _("Wednesday")
    THURSDAY = 3, _("Thursday")
    FRIDAY = 4, _("Friday")
    SATURDAY = 5, _("Saturday")
    SUNDAY = 6, _("Sunday")


def speciality_image_path(instance, filename):
    """Upload scope for speciality tiles (never touches source-controlled static/)."""
    ext = (filename.rsplit(".", 1)[-1] or "jpg").lower()
    return f"specialities/{instance.slug or 'unassigned'}/card.{ext}"


def doctor_profile_image_path(instance, filename):
    """Upload scope for doctor portraits (never touches source-controlled static/)."""
    ext = (filename.rsplit(".", 1)[-1] or "jpg").lower()
    return f"doctors/{instance.slug or 'unassigned'}/profile.{ext}"


def unique_slug(model, value, max_length=160):
    """Return a URL-safe slug unique for ``model`` (appends ``-2``, ``-3`` ...)."""
    base = slugify(value)[:max_length] or "item"
    candidate = base
    counter = 2
    while model.objects.filter(slug=candidate).exists():
        suffix = f"-{counter}"
        candidate = f"{base[: max_length - len(suffix)]}{suffix}"
        counter += 1
    return candidate


class SpecialityQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class Speciality(models.Model):
    """A medical speciality (e.g. Cardiology) shown on the public site."""

    name = models.CharField(_("name"), max_length=120, unique=True)
    slug = models.SlugField(_("slug"), max_length=140, unique=True, blank=True)
    description = models.TextField(_("description"), blank=True)
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Inactive specialities are hidden from the public site."),
    )
    # ADR-022 (C1): administrator-managed card/hero image. Uploads live under
    # MEDIA_ROOT (never source-controlled static/img); unset keeps the
    # documented static fallback chain untouched.
    image = models.ImageField(
        _("image"),
        upload_to=speciality_image_path,
        null=True,
        blank=True,
        help_text=_(
            "Optional administrator-uploaded image used wherever the speciality "
            "tile/hero renders (overrides the static placeholder). Set a short "
            "honest caption to describe it."
        ),
    )
    image_caption = models.CharField(
        _("image caption"),
        max_length=255,
        blank=True,
        help_text=_("Shown with the speciality detail hero when an image is set."),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    objects = SpecialityQuerySet.as_manager()

    class Meta:
        verbose_name = _("speciality")
        verbose_name_plural = _("specialities")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["is_active"], name="clinic_spec_active_idx"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(Speciality, self.name, max_length=140)
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("speciality_detail", kwargs={"slug": self.slug})


class DoctorQuerySet(models.QuerySet):
    def accepting(self):
        return self.filter(is_accepting_appointments=True)

    def public(self):
        """Doctors that may appear on the public site.

        Requires an active user, an active speciality, and the doctor to be
        accepting appointments (per the Phase 4 requirement to display only
        active specialities and accepting doctors).
        """
        return self.filter(
            user__is_active=True,
            speciality__is_active=True,
            is_accepting_appointments=True,
        )


class Doctor(models.Model):
    """A doctor profile linked one-to-one with a DOCTOR-role ``accounts.User``."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor",
        verbose_name=_("user"),
    )
    speciality = models.ForeignKey(
        Speciality,
        on_delete=models.PROTECT,
        related_name="doctors",
        verbose_name=_("speciality"),
    )
    slug = models.SlugField(_("slug"), max_length=160, unique=True, blank=True)
    registration_number = models.CharField(
        _("registration number"), max_length=50, unique=True
    )
    qualification = models.CharField(_("qualification"), max_length=120)
    bio = models.TextField(_("professional biography"), blank=True)
    consultation_fee = models.DecimalField(
        _("consultation fee"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_("Optional consultation fee."),
    )
    slot_length_minutes = models.PositiveSmallIntegerField(
        _("default slot length (minutes)"),
        default=30,
        validators=[MinValueValidator(1)],
    )
    is_accepting_appointments = models.BooleanField(
        _("accepting appointments"), default=True
    )
    # ADR-022 (C1): administrator-managed portrait (supersedes ADR-015).
    # Unset keeps the initials/placeholder fallback chain untouched. An
    # upload is presumed a genuine, consented photograph of this doctor
    # (docs/imagery-licensing.md honesty rules).
    profile_image = models.ImageField(
        _("profile image"),
        upload_to=doctor_profile_image_path,
        null=True,
        blank=True,
        help_text=_(
            "Optional administrator-uploaded portrait of this doctor; overrides "
            "the static placeholder and, when absent, the initials avatar."
        ),
    )
    profile_image_caption = models.CharField(
        _("profile image caption"),
        max_length=255,
        blank=True,
        help_text=_(
            "Optional honest caption describing the portrait "
            "(e.g. source/consent reference for the imagery manifest)."
        ),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    objects = DoctorQuerySet.as_manager()

    class Meta:
        verbose_name = _("doctor")
        verbose_name_plural = _("doctors")
        ordering = ["user__first_name", "user__last_name", "user__email"]
        indexes = [
            models.Index(
                fields=["speciality", "is_accepting_appointments"],
                name="clinic_doc_spec_accept_idx",
            ),
            models.Index(
                fields=["is_accepting_appointments"],
                name="clinic_doc_accept_idx",
            ),
        ]

    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

    def clean(self):
        super().clean()
        # The linked user must hold the DOCTOR role (see docs/architecture.md §6).
        if self.user_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            if self.user.role != User.Role.DOCTOR:
                raise ValidationError(
                    {"user": _("The linked user must have the DOCTOR role.")}
                )

    def save(self, *args, **kwargs):
        if not self.slug and self.user_id:
            self.slug = unique_slug(
                Doctor, self.user.get_full_name() or self.user.email, max_length=160
            )
        self.full_clean()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("doctor_detail", kwargs={"slug": self.slug})


class AvailabilityRule(models.Model):
    """A recurring weekly window from which bookable slots are materialized."""

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="availability_rules",
        verbose_name=_("doctor"),
    )
    weekday = models.PositiveSmallIntegerField(
        _("day of week"),
        choices=Weekday.choices,
        validators=[MaxValueValidator(6)],
    )
    start_time = models.TimeField(_("start time"))
    end_time = models.TimeField(_("end time"))
    slot_length_minutes = models.PositiveSmallIntegerField(
        _("slot length (minutes)"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=_("Blank falls back to the doctor's default slot length."),
    )
    is_active = models.BooleanField(_("active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        verbose_name = _("availability rule")
        verbose_name_plural = _("availability rules")
        ordering = ["doctor", "weekday", "start_time"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="clinic_avail_end_after_start",
            ),
            models.UniqueConstraint(
                fields=["doctor", "weekday", "start_time", "end_time"],
                name="clinic_avail_unique_window",
            ),
        ]
        indexes = [
            models.Index(
                fields=["doctor", "weekday", "is_active"],
                name="clinic_avail_doc_wd_idx",
            ),
        ]

    def __str__(self):
        return f"{self.doctor} — {self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

    @property
    def effective_slot_length_minutes(self):
        """Rule-level slot length, falling back to the doctor's default."""
        return self.slot_length_minutes or self.doctor.slot_length_minutes

    def clean(self):
        super().clean()
        errors = {}
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            errors["end_time"] = _("End time must be later than start time.")
        if self.slot_length_minutes is not None and self.slot_length_minutes <= 0:
            errors["slot_length_minutes"] = _("Slot duration must be positive.")
        if self.doctor_id and self.start_time and self.end_time and not errors:
            overlapping = AvailabilityRule.objects.filter(
                doctor_id=self.doctor_id,
                weekday=self.weekday,
                is_active=True,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            if overlapping.exists():
                errors["start_time"] = _(
                    "This window overlaps an existing availability rule for this doctor."
                )
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class OneDayAvailability(models.Model):
    """
    Availability for a specific calendar date.

    Unlike AvailabilityRule, this record never repeats weekly.
    """

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="one_day_availabilities",
        verbose_name=_("doctor"),
    )

    date = models.DateField(_("date"))

    start_time = models.TimeField(_("start time"))

    end_time = models.TimeField(_("end time"))

    slot_length_minutes = models.PositiveSmallIntegerField(
        _("slot length (minutes)"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text=_(
            "Leave blank to use the doctor's default slot length."
        ),
    )

    is_active = models.BooleanField(
        _("active"),
        default=True,
    )

    created_at = models.DateTimeField(
        _("created at"),
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        _("updated at"),
        auto_now=True,
    )

    class Meta:
        verbose_name = _("one-day availability")
        verbose_name_plural = _("one-day availability")
        ordering = ["date", "start_time"]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    end_time__gt=models.F("start_time")
                ),
                name="clinic_one_day_end_after_start",
            ),
        ]

        indexes = [
            models.Index(
                fields=["doctor", "date", "is_active"],
                name="clinic_one_day_doc_date_idx",
            ),
        ]

    def __str__(self):
        return (
            f"{self.doctor} — {self.date} "
            f"{self.start_time:%H:%M}-{self.end_time:%H:%M}"
        )

    @property
    def effective_slot_length_minutes(self):
        """
        Use the date-specific slot duration when supplied;
        otherwise use the doctor's default duration.
        """
        return (
            self.slot_length_minutes
            or self.doctor.slot_length_minutes
        )

    def clean(self):
        super().clean()

        errors = {}

        if (
            self.start_time
            and self.end_time
            and self.end_time <= self.start_time
        ):
            errors["end_time"] = _(
                "End time must be later than start time."
            )

        if (
            self.slot_length_minutes is not None
            and self.slot_length_minutes <= 0
        ):
            errors["slot_length_minutes"] = _(
                "Slot duration must be positive."
            )

        if (
            self.doctor_id
            and self.date
            and self.start_time
            and self.end_time
            and not errors
        ):
            # A doctor's leave takes precedence over availability.
            on_leave = DoctorLeave.objects.filter(
                doctor_id=self.doctor_id,
                start_date__lte=self.date,
                end_date__gte=self.date,
            ).exists()

            if on_leave:
                errors["date"] = _(
                    "This doctor is on leave on the selected date."
                )

            # Avoid overlapping active weekly availability windows.
            weekday = self.date.weekday()

            weekly_overlap = AvailabilityRule.objects.filter(
                doctor_id=self.doctor_id,
                weekday=weekday,
                is_active=True,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            ).exists()

            if weekly_overlap:
                errors["start_time"] = _(
                    "This time overlaps an active weekly availability rule."
                )

            # Avoid overlapping one-day availability windows.
            one_day_rules = OneDayAvailability.objects.filter(
                doctor_id=self.doctor_id,
                date=self.date,
                is_active=True,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            )

            if self.pk:
                one_day_rules = one_day_rules.exclude(pk=self.pk)

            if one_day_rules.exists():
                errors["start_time"] = _(
                    "This time overlaps another active one-day availability rule."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class DoctorLeave(models.Model):
    """An inclusive date range during which a doctor is unavailable."""

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="leaves",
        verbose_name=_("doctor"),
    )
    start_date = models.DateField(_("start date"))
    end_date = models.DateField(_("end date"))
    reason = models.CharField(_("reason"), max_length=255, blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("doctor leave")
        verbose_name_plural = _("doctor leave")
        ordering = ["-start_date"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="clinic_leave_end_gte_start",
            ),
        ]
        indexes = [
            models.Index(
                fields=["doctor", "start_date", "end_date"],
                name="clinic_leave_doc_dates_idx",
            ),
        ]

    def __str__(self):
        return f"{self.doctor} leave {self.start_date}–{self.end_date}"

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError(
                {"end_date": _("End date cannot be before start date.")}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
