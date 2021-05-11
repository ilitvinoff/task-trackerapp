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

    def has_object_permission(self, request, view, obj):
        return obj.get_owner() == request.user


class IsTaskOwnerOrAssigneeREST(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve' or view.action == 'partial_update':
            return obj and (obj.get_owner() == request.user or obj.get_assignee() == request.user)
        return obj and obj.get_owner() == request.user


class IsOwnerOrAssigneeREST(permissions.BasePermission):
    """
    Custom permission to instance's list in one case(watch below 'if ...', and edit/delete/create if current user is -
    instance user
    """

    def has_object_permission(self, request, view, obj):
        return obj and (
                obj.get_owner() == request.user or obj.get_assignee() == request.user or obj.get_related_obj_owner() == request.user)
