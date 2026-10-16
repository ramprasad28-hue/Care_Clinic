"""Authentication views.

Login, logout, and password reset use Django's built-in views (wired in
``accounts/urls.py``). Only the public registration view is custom.
"""
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import PatientRegistrationForm


class RegisterView(CreateView):
    """Public patient registration.

    On success the new Patient is signed in and sent home. The role is set by
    the form (hard-coded PATIENT); the view never accepts a role from input.
    """

    form_class = PatientRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request, "Welcome to Care_Clinic. Your patient account is ready."
        )
        return response
