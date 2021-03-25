from rest_framework import permissions
from django.contrib.auth.decorators import user_passes_test


class IsOwnerOrAssignee(permissions.BasePermission):
    """
    Custom permission to allow owners/assignee manipulate with obj only
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or obj.assignee == request.user


class IsOwner(permissions.BasePermission):
    """
    Custom permission to allow owner manipulate with obj only
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsTaskOwnerOrTaskAssignee(permissions.BasePermission):
    """
    Custom permission to show message, if message is relative to task and request user is task owner or task
    is assigned to him
    """

    def has_object_permission(self, request, view, obj):
        return obj.task.owner == request.user or obj.task.assignee == request.user
