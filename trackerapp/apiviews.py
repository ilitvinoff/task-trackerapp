from .serializers import (
    UserSerializer,
    GroupSerializer,
    TaskSerializer,
    MessageSerializer, ProfileSerializer, AttachmentSerializer,
)
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import User, Group
from rest_framework import viewsets, mixins, permissions
from .permissions import (
    IsOwnerOrAssigneeREST,
    IsTaskOwnerOrTaskAssigneeREST, IsOwnerREST,
)
from .models import Message, TaskModel, UserProfile, Attachment
from django.db.models import Q


class MessageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows messages to be viewed or edited.
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOwnerOrTaskAssigneeREST]

    def get_queryset(self):
        return (
            Message.objects.all()
                .filter(
                Q(task__owner__exact=self.request.user)
                | Q(task__assignee__exact=self.request.user),
            )
                .order_by("creation_date")
        )

    def destroy(self, request, *args, **kwargs):
        if self.get_object().owner == request.user:
            return super().destroy(request, args, kwargs)
        raise PermissionDenied()

    def update(self, request, *args, **kwargs):
        if self.get_object().owner == request.user:
            return super().update(request, args, kwargs)
        raise PermissionDenied()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = TaskModel.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssigneeREST]

    def get_queryset(self):
        return TaskModel.objects.all().filter(
            Q(owner__exact=self.request.user) | Q(assignee__exact=self.request.user)
        )

    def destroy(self, request, *args, **kwargs):
        if self.get_object().owner == request.user:
            return super().destroy(request, args, kwargs)
        raise PermissionDenied()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class UserViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class GroupViewSet(
    mixins.RetrieveModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet
):
    """
    API endpoint that allows groups to be viewed or edited.
    """

    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerREST]

    def get_queryset(self):
        return UserProfile.objects.all().filter(owner__exact=self.request.user)

    def destroy(self, request, *args, **kwargs):
        if self.get_object().owner == request.user:
            return super().destroy(request, args, kwargs)
        raise PermissionDenied()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer
    permission_classes = (permissions.IsAuthenticated, IsTaskOwnerOrTaskAssigneeREST)

    def get_queryset(self):
        return (
            Attachment.objects.all()
                .filter(
                Q(task__owner__exact=self.request.user)
                | Q(task__assignee__exact=self.request.user),
            )
                .order_by("creation_date")
        )

    def destroy(self, request, *args, **kwargs):
        if self.get_object().get_owner() == request.user:
            return super().destroy(request, args, kwargs)
        raise PermissionDenied()

    def update(self, request, *args, **kwargs):
        if self.get_object().owner == request.user  or self.get_object().get_assignee()==request.user:
            return super().update(request, args, kwargs)
        raise PermissionDenied()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
