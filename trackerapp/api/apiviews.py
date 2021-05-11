from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rest_framework import viewsets, mixins, permissions, status, response, generics
from rest_framework.permissions import IsAuthenticated

from trackerapp.api.permissions import (
    IsOwnerOrAssigneeREST, FullPermissionDenied, IsOwnerREST, IsTaskOwnerOrAssigneeREST,
)
from trackerapp.api.serializers import (
    UserSerializer,
    GroupSerializer,
    TaskSerializer,
    MessageSerializer, ProfileSerializer, AttachmentSerializer, UserRegisterSerializer, TaskHistorySerializer,
    AttachmentHistorySerializer,
)
from trackerapp.models import Message, TaskModel, UserProfile, Attachment


class RelatedModelViewSet(viewsets.ModelViewSet):
    """
    Class define functionality of related to some objects objects.
    For example attachment is relate to task, message is relate to task, etc
    """
    related_model = None  # for example TaskModel
    base_model = None  # for example if related model is TaskModel than base_model - is Attachment or Message
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssigneeREST]

    def get_related_instance(self):
        return self.related_model.objects.filter(id__exact=self.kwargs['pk']).first()

    def get_object(self):
        """
        get base model instance
        :return:
        """
        obj = self.base_model.objects.filter(id=self.kwargs['pk']).first()
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        """
        get queryset of base_model instances related to related_model
        :return:
        """
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
        """
                Check if request user has corresponding permissions. If has set him as attachment owner, and
                set related task directly
                :param serializer:
                :return:
                """
        try:
            related_task = TaskModel.objects.get(id=serializer.initial_data["task_id"])
        except:
            raise PermissionDenied("Bad request")

        request_user = self.request.user

        if related_task and (request_user == related_task.get_owner() or request_user == related_task.get_assignee()):
            serializer.save(owner=request_user, task=related_task)
        else:
            raise PermissionDenied("Have no permission to set attachment to the task(id)={}".format(related_task.id))


class MessageViewSet(RelatedModelViewSet):
    """
    API endpoint that allows messages to be viewed or edited.
    """
    base_model = Message
    related_model = TaskModel
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def perform_create(self, serializer):
        """
        Check if request user has corresponding permissions. If has set him as message owner, and
        set related task directly
        :param serializer:
        :return:
        """
        try:
            related_task = TaskModel.objects.get(id=serializer.initial_data["task_id"])
        except:
            raise PermissionDenied("Bad request")

        request_user = self.request.user

        if related_task and (request_user == related_task.get_owner() or request_user == related_task.get_assignee()):
            serializer.save(owner=request_user, task=related_task)
        else:
            raise PermissionDenied("Have no permission to set message to the task(id)={}".format(related_task.id))


class TaskViewSet(viewsets.ModelViewSet):
    queryset = TaskModel.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOwnerOrAssigneeREST]

    def perform_create(self, serializer):
        """
        To set owner as request user (when task is creating) directly
        :param serializer:
        :return:
        """
        serializer.save(owner=self.request.user)

    def get_object(self):
        """
        Check if incorrect pk value, than raise error.
        super().get_object - return 404 status code
        :return:
        """
        pk = self.kwargs.get('pk', None)

        if not pk:
            raise ValueError("pk not present in request to identifier task")

        obj = TaskModel.objects.get(id=pk)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_queryset(self):
        """Get owned by / assigned to user tasks"""
        return TaskModel.objects.all().filter(
            Q(owner__exact=self.request.user) | Q(assignee__exact=self.request.user)
        )


class TaskHistoryListAPIView(generics.ListAPIView):
    """
    To view list of events in history for task and related to it attachments
    """
    task_serializer_class = TaskHistorySerializer
    attachment_serializer_class = AttachmentHistorySerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOwnerOrAssigneeREST]

    def get_queryset_task(self):
        return TaskModel.objects.filter(id=self.kwargs['pk'])

    def get_queryset_attachment(self):
        return Attachment.objects.filter(task_id__exact=TaskModel.objects.filter(id=self.kwargs['pk']).first().id)

    def list(self, request, *args, **kwargs):
        """
        Here form result list, which consists of the task's history and
        of the related to the task attachment's history, ordered by history date
        """
        history_list = []
        tasks = self.task_serializer_class(self.get_queryset_task(), many=True)
        attachments = self.attachment_serializer_class(self.get_queryset_attachment(), many=True)

        # Get the history of tasks and attachments from the corresponding query sets
        # type(task.data) = rest_framework.utils.serializers_helpers.ReturnList
        # type(tasks.data[0]) = collections.OrderedDict
        history_list.extend(list(list(tasks.data)[0]['history']))
        history_list.extend(list(list(attachments.data)[0]['history']))

        history_list.sort(key=lambda a: a['history_date'], reverse=True)
        print(history_list)
        return response.Response({'history': history_list})


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
    permission_classes = [IsAuthenticated, IsOwnerREST]

    def get_permissions(self):
        """
        Override for 'create action' so that anyone(not authenticated) can register a new profile.
        For retrieve - if authenticated...
        :return: list of rest_framework.permissions.BasePermission
        """
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated(), ]

        if self.action == 'create':
            return []
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """
        Override super create to use another then self.serializer_class,
        but UserRegisterSerializer
        :return rest_framework.response.Response
        """
        serializer = UserRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
