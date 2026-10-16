"""Doctor self-service views for availability and leave.

Authorization is enforced on the backend:

* ``RoleRequiredMixin`` (Phase 3) restricts every view to the DOCTOR role
  (superusers pass); anonymous users are redirected to login, wrong roles get
  HTTP 403.
* Every queryset is filtered by ``doctor__user=request.user``, so a doctor
  editing/deleting a URL belonging to another doctor gets **404**, not a leak.
* Create/update views force ``instance.doctor`` from ``request.user`` and the
  forms do not expose a ``doctor`` field, so a submitted doctor id is ignored.
"""
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.models import User
from accounts.permissions import RoleRequiredMixin

from .forms import AvailabilityRuleForm, DoctorLeaveForm
from .models import AvailabilityRule, DoctorLeave


class DoctorSelfServiceMixin(RoleRequiredMixin):
    """Base for doctor-only views; resolves the caller's own Doctor profile."""

    allowed_roles = (User.Role.DOCTOR,)

    def get_doctor(self):
        doctor = getattr(self.request.user, "doctor", None)
        if doctor is None:
            raise PermissionDenied("This account has no doctor profile.")
        return doctor


# --------------------------------------------------------------------------
# Availability rules
# --------------------------------------------------------------------------
class AvailabilityListView(DoctorSelfServiceMixin, ListView):
    template_name = "clinic/availability_list.html"
    context_object_name = "rules"

    def get_queryset(self):
        return AvailabilityRule.objects.filter(doctor=self.get_doctor()).order_by(
            "weekday", "start_time"
        )


class AvailabilityCreateView(DoctorSelfServiceMixin, CreateView):
    model = AvailabilityRule
    form_class = AvailabilityRuleForm
    template_name = "clinic/availability_form.html"
    success_url = reverse_lazy("clinic:availability_list")

    def form_valid(self, form):
        form.instance.doctor = self.get_doctor()
        return super().form_valid(form)


class AvailabilityUpdateView(DoctorSelfServiceMixin, UpdateView):
    model = AvailabilityRule
    form_class = AvailabilityRuleForm
    template_name = "clinic/availability_form.html"
    success_url = reverse_lazy("clinic:availability_list")

    def get_queryset(self):
        return AvailabilityRule.objects.filter(doctor=self.get_doctor())

    def form_valid(self, form):
        form.instance.doctor = self.get_doctor()
        return super().form_valid(form)


class AvailabilityDeleteView(DoctorSelfServiceMixin, DeleteView):
    model = AvailabilityRule
    template_name = "clinic/availability_confirm_delete.html"
    success_url = reverse_lazy("clinic:availability_list")

    def get_queryset(self):
        return AvailabilityRule.objects.filter(doctor=self.get_doctor())


# --------------------------------------------------------------------------
# Leave
# --------------------------------------------------------------------------
class LeaveListView(DoctorSelfServiceMixin, ListView):
    template_name = "clinic/leave_list.html"
    context_object_name = "leaves"

    def get_queryset(self):
        return DoctorLeave.objects.filter(doctor=self.get_doctor()).order_by("-start_date")


class LeaveCreateView(DoctorSelfServiceMixin, CreateView):
    model = DoctorLeave
    form_class = DoctorLeaveForm
    template_name = "clinic/leave_form.html"
    success_url = reverse_lazy("clinic:leave_list")

    def form_valid(self, form):
        form.instance.doctor = self.get_doctor()
        return super().form_valid(form)


class LeaveDeleteView(DoctorSelfServiceMixin, DeleteView):
    model = DoctorLeave
    template_name = "clinic/leave_confirm_delete.html"
    success_url = reverse_lazy("clinic:leave_list")

    def get_queryset(self):
        return DoctorLeave.objects.filter(doctor=self.get_doctor())
