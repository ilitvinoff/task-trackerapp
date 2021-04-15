from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from rest_framework import permissions


class IsOwnerOrAssigneeREST(permissions.BasePermission):
    """
    Custom permission to allow owners/assignee manipulate with obj only
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or obj.assignee == request.user


class IsOwnerREST(permissions.BasePermission):
    """
    Custom permission to allow owner manipulate with obj only
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsTaskOwnerOrTaskAssigneeREST(permissions.BasePermission):
    """
    Custom permission to show message, if message is relative to task and request user is task owner or task
    is assigned to him
    """

    def has_object_permission(self, request, view, obj):
        return obj.task.owner == request.user or obj.task.assignee == request.user


class IsOwnerPermissionRequiredMixin(PermissionRequiredMixin):
    """
    Custom permission to check if request user is owner of instance
    """

    def has_permission(self):
        """
        Override this method to customize the way permissions are checked.
        """
        return self.request.user.is_authenticated

    def dispatch(self, request, *args, **kwargs):
        try:
            pk = kwargs.get("pk")

            if self.permission_class_model:
                owner = self.permission_class_model.objects.get(pk=pk).get_owner()
            else:
                raise NotImplemented("permission class model is not implemented")

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
            pk = kwargs.get("pk")

            if self.permission_class_model:
                assigned_user = self.permission_class_model.objects.get(pk=pk).get_assignee()
                owner = self.permission_class_model.objects.get(pk=pk).get_owner()
            else:
                raise NotImplemented("permission class model is not implemented")

            if not (request.user == owner or request.user == assigned_user):
                return self.handle_no_permission()

            return super().dispatch(request, *args, **kwargs)

        except KeyError:
            raise PermissionDenied("Bad request. Have no permission. No assigned user/owner found.")
