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
            owner = kwargs["owner"]
            if self.request.user != owner:
                return self.handle_no_permission()

            return super().dispatch(request, *args, **kwargs)

        except KeyError:
            raise PermissionDenied("Have no permission. No owner found.")


class IsOwnerOrAssigneePermissionRequiredMixin(PermissionRequiredMixin):
    """
    Custom permission to check if request user is owner or assignee of the instance
    """

    def has_permission(self):
        return self.request.user.is_authenticated

    def dispatch(self, request, *args, **kwargs):
        try:
            assigned_user = kwargs["assigned_user"]
            owner = kwargs['owner']
            if not (request.user == owner or request.user == assigned_user):
                return self.handle_no_permission()

            return super().dispatch(request, *args, **kwargs)

        except KeyError:
            raise PermissionDenied("Have no permission. No assigned user/owner found.")



def custom_permissions_dispatch(
        main_class_instance, permission_parent_class, model_class, request, has_assignee=False, *args, **kwargs
):
    """
    custom_permissions_dispatch (...) - use in views. Requires model_class from attrs to get owner / assignee from this model
       and assign it the value ** kwargs. Then use the dispatch (...) method 'permission_parent_class' (our custom permission classes)
       with modified ** kwargs to analyze if the user has permission. Model_class's class must define get_assignee() and get_owner() methods.

    :param main_class_instance: View class's instance
    :param permission_parent_class: permission class - parent of view class
    :param model_class: class of the model where from we'll get owner/assignee
    :param request: client request
    :param has_assignee: bool
    :param args:
    :param kwargs:
    """
    pk = kwargs.get("pk")

    try:
        if has_assignee:
            kwargs["assigned_user"] = model_class.objects.get(pk=pk).get_assignee()

        kwargs['owner'] = model_class.objects.get(pk=pk).get_owner()

        return permission_parent_class.dispatch(main_class_instance, request, *args, **kwargs)
    except model_class.DoesNotExist:
        raise PermissionDenied("Have no permission. Object (task, msg, etc...) does not exist.")
