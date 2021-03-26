from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from rest_framework import permissions
from django.db.models import Q


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
        obj = kwargs["obj"]
        if obj.owner:
            if self.request.user != obj.owner:
                return self.handle_no_permission()
        else:
            raise PermissionDenied("Corrupted object. Bad request.")
        return super().dispatch(request, *args, **kwargs)


class IsOwnerOrAssigneePermissionRequiredMixin(PermissionRequiredMixin):
    """
    Custom permission to check if request user is owner or assignee of the instance
    """

    def has_permission(self):
        return self.request.user.is_authenticated

    def dispatch(self, request, *args, **kwargs):
        obj = kwargs["obj"]
        assignee = kwargs['assignee']

        if not (request.user == obj.owner or request.user == assignee):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


def dispatch_override(
        main_class_instance, parent_class, model_class, request, assigneeModel=False, *args, **kwargs
):
    pk = kwargs.get("pk")

    try:
        obj = model_class.objects.get(owner_id=pk)
        kwargs["obj"] = obj
        if assigneeModel:
            kwargs['assignee'] = obj.task.assignee
        return parent_class.dispatch(main_class_instance, request, *args, **kwargs)
    except model_class.DoesNotExist:
        raise PermissionDenied("Have no permission")
