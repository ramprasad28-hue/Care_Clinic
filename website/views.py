"""Public, read-only views for the clinic catalog.

All pages are accessible to anonymous visitors and authenticated users alike.
Doctor data is read through ``Doctor.objects.public()`` so only doctors with an
active user, an active speciality, and ``is_accepting_appointments=True`` are
ever shown.
"""
from django.views.generic import DetailView, ListView, TemplateView

from clinic.models import Doctor, Speciality


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["specialities"] = Speciality.objects.active()[:6]
        context["doctors"] = Doctor.objects.public()[:6]
        return context


class SpecialityListView(ListView):
    template_name = "website/speciality_list.html"
    context_object_name = "specialities"

    def get_queryset(self):
        return Speciality.objects.active()


class SpecialityDetailView(DetailView):
    template_name = "website/speciality_detail.html"
    context_object_name = "speciality"

    def get_queryset(self):
        return Speciality.objects.active()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["doctors"] = Doctor.objects.public().filter(speciality=self.object)
        return context


class DoctorListView(ListView):
    template_name = "website/doctor_list.html"
    context_object_name = "doctors"

    def get_queryset(self):
        queryset = Doctor.objects.public()
        selected = self._selected_speciality()
        if selected:
            queryset = queryset.filter(speciality__slug=selected)
        return queryset

    def _selected_speciality(self):
        return self.request.GET.get("speciality", "").strip()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["specialities"] = Speciality.objects.active()
        context["selected_speciality"] = self._selected_speciality()
        return context


class DoctorDetailView(DetailView):
    template_name = "website/doctor_detail.html"
    context_object_name = "doctor"

    def get_queryset(self):
        return Doctor.objects.public()
