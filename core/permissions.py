from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


def get_user_hospital(user):
    if getattr(user, "hospital_id", None):
        return user.hospital
    perfil_medico = getattr(user, "perfil_medico", None)
    if perfil_medico and getattr(perfil_medico, "hospital_id", None):
        return perfil_medico.hospital
    return None


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            if request.user.tipo not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def hospital_scope_required(obj_hospital_field="hospital", model=None, lookup_kwarg="pk"):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied
            if model:
                obj = get_object_or_404(model, pk=kwargs.get(lookup_kwarg))
                user_hospital = get_user_hospital(request.user)
                obj_hospital = getattr(obj, obj_hospital_field, None)
                if not user_hospital or not obj_hospital or obj_hospital.id != user_hospital.id:
                    raise PermissionDenied
                request._scoped_object = obj
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


class TipoRequiredMixin:
    allowed_roles = ()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        if request.user.tipo not in self.allowed_roles:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class HospitalScopeRequiredMixin:
    obj_hospital_field = "hospital"
    model = None
    lookup_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied
        if self.model:
            obj = get_object_or_404(self.model, pk=kwargs.get(self.lookup_kwarg))
            user_hospital = get_user_hospital(request.user)
            obj_hospital = getattr(obj, self.obj_hospital_field, None)
            if not user_hospital or not obj_hospital or obj_hospital.id != user_hospital.id:
                raise PermissionDenied
            request._scoped_object = obj
        return super().dispatch(request, *args, **kwargs)
