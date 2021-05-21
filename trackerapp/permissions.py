from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404


class IsTaskOwnerOrAssignee(PermissionRequiredMixin):

    def has_permission(self):
        return self.request.user.is_authenticated

    def dispatch(self, request, *args, **kwargs):
        try:
            pk = kwargs["pk"]

            if self.permission_model:
                assigned_user = self.permission_model.objects.get(pk=pk).get_assignee()
                owner = self.permission_model.objects.get(pk=pk).get_owner()
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

            if self.permission_model:
                owner = self.permission_model.objects.get(pk=pk).get_owner()
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

            if self.permission_model:
                assigned_user = self.permission_model.objects.get(pk=pk).get_assignee()
                owner = self.permission_model.objects.get(pk=pk).get_owner()
                related_obj_owner = self.permission_model.objects.get(pk=pk).get_related_obj_owner()
            else:
                raise NotImplemented("invalid permission class model")

            if not (request.user == owner or request.user == assigned_user or request.user == related_obj_owner):
                return self.handle_no_permission()

            return super().dispatch(request, *args, **kwargs)

        except Exception:
            raise PermissionDenied("Bad request.")


class ChatRoomPermission(PermissionRequiredMixin):
    def has_permission(self):
        return self.request.user.is_authenticated

    def dispatch(self, request, *args, **kwargs):
        try:
            pk = kwargs["pk"]

            if self.permission_model:
                room = self.permission_model.objects.get(pk=pk)
                owner = room.get_owner()
                members = room.get_members()
            else:
                raise NotImplemented("invalid permission class model")

            if not room:
                raise Http404("Room not found. ID={} does not exists".format(pk))

            if room and room.is_private and not (owner == request.user or request.user in members):
                return self.handle_no_permission()

            return super().dispatch(request, *args, **kwargs)

        except Exception:
            raise PermissionDenied("Bad request.")
