"""Backend-enforced role-based access control primitives.

Two complementary mechanisms are provided:

* :func:`role_required` — a function-view decorator.
* :class:`RoleRequiredMixin` — a mixin for class-based views.

Both deny **anonymous** users by redirecting them to the login page and deny
**authenticated-but-wrong-role** users with HTTP 403 (``PermissionDenied``).
Superusers and the ADMIN role always pass (see ``User.has_role``).

Scoped querysets (the ``for_user`` contract) live on the domain models they
protect — e.g. ``Appointment.objects.for_user(user)`` in the ``appointments``
app (Phase 5). Ownership filtering is applied by *querying through* that
scoped queryset (``get_object_or_404(Appointment.objects.for_user(user), ...)``)
so that unauthorized identifiers return 404 instead of leaking existence.
"""
from functools import wraps

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied


def user_has_any_role(user, roles):
    """True if ``user`` is authenticated and holds one of ``roles``.

    Superusers pass regardless of ``roles``.
    """
    return user.is_authenticated and user.has_role(*roles)


def role_required(*roles):
    """Restrict a function view to the given role(s).

    Usage::

        @role_required(User.Role.DOCTOR, User.Role.ADMIN)
        def schedule(request): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
            if not user_has_any_role(request.user, roles):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


class RoleRequiredMixin(LoginRequiredMixin):
    """Class-based view mixin restricting access to ``allowed_roles``.

    Usage::

        class DoctorScheduleView(RoleRequiredMixin, ListView):
            allowed_roles = (User.Role.DOCTOR,)
    """

    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        # LoginRequiredMixin handles the anonymous -> login redirect in super().
        if request.user.is_authenticated and not user_has_any_role(
            request.user, self.allowed_roles
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
