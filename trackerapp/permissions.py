from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from rest_framework import permissions


class FullPermissionDenied(permissions.BasePermission):
    def has_permission(self, request, view):
        return False

    def has_object_permission(self, request, view, obj):
        return False


class IsOwnerREST(permissions.BasePermission):
    """
    Custom permission to allow owner manipulate with obj only
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        raise PermissionDenied()

    def has_object_permission(self, request, view, obj):
        return obj.get_owner() == request.user


class IsTaskOwnerOrAssigneeREST(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        raise PermissionDenied()

    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve' or view.action == 'partial_update':
            return obj and (obj.get_owner() == request.user or obj.get_assignee() == request.user)
        return obj and obj.get_owner() == request.user


class IsOwnerOrAssigneeREST(permissions.BasePermission):
    """
    Custom permission to instance's list in one case(watch below 'if ...', and edit/delete/create if current user is -
    instance user
    """

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            return True
        raise PermissionDenied()

    def has_object_permission(self, request, view, obj):
        return obj and (
                obj.get_owner() == request.user or obj.get_assignee() == request.user or obj.get_related_obj_owner() == request.user)


class IsTaskOwnerOrAssignee(PermissionRequiredMixin):

    def has_permission(self):
        return self.request.user.is_authenticated

    def dispatch(self, request, *args, **kwargs):
        try:
            pk = kwargs["pk"]

            if self.permission_class_model:
                assigned_user = self.permission_class_model.objects.get(pk=pk).get_assignee()
                owner = self.permission_class_model.objects.get(pk=pk).get_owner()
            else:
                raise NotImplemented("invalid permission class model")

            if not (request.user == owner or request.user == assigned_user):
                return self.handle_no_permission()

            return super().dispatch(request, *args, **kwargs)

        except Exception as e:
            raise PermissionDenied("Bad request." + e.__str__())


class IsOwnerPermissionRequiredMixin(PermissionRequiredMixin):
    """
    Custom permission to check if request user is owner of instance
    """

    def has_permission(self):
        return self.request.user.is_authenticated

    def dispatch(self, request, *args, **kwargs):
        try:
            pk = kwargs["pk"]

            if self.permission_class_model:
                owner = self.permission_class_model.objects.get(pk=pk).get_owner()
            else:
                raise NotImplemented("invalid permission class model")

            if self.request.user != owner:
                return self.handle_no_permission()

            return super().dispatch(request, *args, **kwargs)

        except Exception:
            raise PermissionDenied("Bad request. Have no permission. No owner found.")


class IsOwnerOrAssigneePermissionRequiredMixin(PermissionRequiredMixin):
    """
    Custom permission to check if request user is owner or assignee of the instance
    """

    def has_permission(self):
        return self.request.user.is_authenticated

    def dispatch(self, request, *args, **kwargs):
        try:
            pk = kwargs["pk"]

            if self.permission_class_model:
                assigned_user = self.permission_class_model.objects.get(pk=pk).get_assignee()
                owner = self.permission_class_model.objects.get(pk=pk).get_owner()
                related_obj_owner = self.permission_class_model.objects.get(pk=pk).get_related_obj_owner()
            else:
                raise NotImplemented("invalid permission class model")

            if not (request.user == owner or request.user == assigned_user or request.user == related_obj_owner):
                return self.handle_no_permission()

            return super().dispatch(request, *args, **kwargs)

        except Exception:
            raise PermissionDenied("Bad request.")
