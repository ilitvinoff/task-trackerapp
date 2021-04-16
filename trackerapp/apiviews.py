from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework import viewsets, mixins, permissions

from .models import Message, TaskModel, UserProfile, Attachment
from .permissions import (
    IsOwnerOrAssigneeREST, FullPermissionDenied, IsOwnerREST,
)
from .serializers import (
    UserSerializer,
    GroupSerializer,
    TaskSerializer,
    MessageSerializer, ProfileSerializer, AttachmentSerializer,
)


class RelatedModelViewSet(viewsets.ModelViewSet):
    related_model = None
    base_model = None
    permission_classes = [IsOwnerOrAssigneeREST]

    def get_related_instance(self):
        return self.related_model.objects.filter(id__exact=self.kwargs['pk']).first()

    def get_object(self):
        obj = self.base_model.objects.filter(id=self.kwargs['pk']).first()
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        related_model_instance = None
        request_user = self.request.user

        try:
            related_model_instance = self.get_related_instance()
        except KeyError:
            pass

        if related_model_instance and not (
                related_model_instance.owner == request_user or related_model_instance.assignee == request_user):
            raise PermissionDenied('Trying request disallowed related {}'.format(type(related_model_instance).__name__))

        request_user = self.request.user

        query = (
                Q(task_id=related_model_instance.id) & (
                Q(task__owner__exact=request_user) | Q(task__assignee__exact=request_user))) \
            if related_model_instance else (Q(task__owner__exact=request_user) | Q(task__assignee__exact=request_user))

        return self.base_model.objects.filter(query).order_by("creation_date")


class AttachmentViewSet(RelatedModelViewSet):
    base_model = Attachment
    related_model = TaskModel
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

    def perform_create(self, serializer):
        related_task = serializer.validated_data.get('task', None)
        request_user = self.request.user

        if related_task and (request_user == related_task.get_owner() or request_user == related_task.get_assignee()):
            serializer.save(owner=request_user, task=related_task)
        else:
            raise PermissionDenied()


class MessageViewSet(RelatedModelViewSet):
    """
    API endpoint that allows messages to be viewed or edited.
    """
    base_model = Message
    related_model = TaskModel
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        related_task = serializer.validated_data.get('task', None)
        request_user = self.request.user

        if related_task and (request_user == related_task.get_owner() or request_user == related_task.get_assignee()):
            serializer.save(owner=request_user, task=related_task)
        else:
            raise PermissionDenied()


class TaskViewSet(viewsets.ModelViewSet):
    queryset = TaskModel.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsOwnerOrAssigneeREST]

    def get_object(self):
        obj = TaskModel.objects.get(id=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        return TaskModel.objects.all().filter(
            Q(owner__exact=self.request.user) | Q(assignee__exact=self.request.user)
        )

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
    permission_classes = [FullPermissionDenied]


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
    permission_classes = [IsOwnerREST]

    def get_object(self):
        obj = UserProfile.objects.get(id=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        return UserProfile.objects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
