"""Public URL configuration (flat, un-namespaced) so the project-wide
``home`` route name relied on by Phase 2/3 code and tests is preserved."""
from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("faq/", views.FaqView.as_view(), name="faq"),
    path("specialities/", views.SpecialityListView.as_view(), name="speciality_list"),
    path(
        "specialities/<slug:slug>/",
        views.SpecialityDetailView.as_view(),
        name="speciality_detail",
    ),
    path("doctors/", views.DoctorListView.as_view(), name="doctor_list"),
    path("doctors/<slug:slug>/", views.DoctorDetailView.as_view(), name="doctor_detail"),
]
