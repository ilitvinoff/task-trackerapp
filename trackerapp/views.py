import logging

from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls.base import reverse_lazy

from trackerapp import filters
from .extended_generics import (
    ExtendedDetailView,
    ExtendedCreateView,
    ExtendedUpdateView,
    ExtendedDeleteView,
    ListInDetailView, ExtendedTaskHistoryListView, ExtendedFilterListView,
)
from .forms import (
    UserProfileEditionForm,
    UserSignUpForm,
)
from .models import TaskModel, Message, UserProfile, Attachment
from .permissions import (
    IsOwnerOrAssigneePermissionRequiredMixin,
    IsOwnerPermissionRequiredMixin, IsTaskOwnerOrAssignee,
)

ITEMS_ON_PAGE = 5


class TaskListView(LoginRequiredMixin, ExtendedFilterListView):
    """
    ListView of created by user tasks, contains form to filter tasks
    """

    model = TaskModel
    filterset_class = filters.TaskFilter
    paginate_by = ITEMS_ON_PAGE
    template_name = "trackerapp/taskmodel_list.html"

    def get_queryset(self):
        tasklist = self.model.objects.filter(owner=self.request.user)
        filtered_list = filters.TaskFilter(self.request.GET, queryset=tasklist)
        return filtered_list.qs


class AssigneeTaskListView(LoginRequiredMixin, ExtendedFilterListView):
    """
    ListView of assigned to user tasks, contains form to filter tasks
    """

    model = TaskModel
    filterset_class = filters.TaskFilter
    context_object_name = "assigned_tasks"
    template_name = "trackerapp/assigned_list.html"
    paginate_by = ITEMS_ON_PAGE

    def get_queryset(self):
        tasklist = self.model.objects.filter(assignee=self.request.user)
        filtered_list = filters.TaskFilter(self.request.GET, queryset=tasklist)
        return filtered_list.qs


class TaskDetail(IsTaskOwnerOrAssignee, ListInDetailView):
    model = permission_model = TaskModel
    defaultModel = Message

    # Add attachment list to context
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data['attachment_list'] = Attachment.objects.filter(task=self.get_object())
        return context_data


class TaskCreate(LoginRequiredMixin, ExtendedCreateView):
    """
    Form to create task.
    """

    model = TaskModel
    fields = [
        "title",
        "description",
        "status",
        "assignee",
    ]

    # override form_valid, to save owner(creator) of the task
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(TaskCreate, self).form_valid(form)


class TaskUpdate(IsOwnerPermissionRequiredMixin, ExtendedUpdateView):
    """
    Edit task form
    """

    model = permission_model = TaskModel
    fields = ["title", "description", "status", "assignee"]

    # after successful edition redirects to the edited task page
    def get_success_url(self):
        return reverse_lazy("task-detail", args=(self.object.id,))


class TaskStatusUpdate(IsTaskOwnerOrAssignee, ExtendedUpdateView):
    """
    Form to edit task status (for assignee...)
    """

    model = permission_model = TaskModel
    fields = [
        "status",
    ]


class TaskDelete(IsOwnerPermissionRequiredMixin, ExtendedDeleteView):
    """
    Form to delete task
    """

    model = permission_model = TaskModel
    success_url = reverse_lazy("index")


class MessageListView(IsTaskOwnerOrAssignee, ExtendedFilterListView):
    model = Message
    filterset_class = filters.MessageDateFilter
    paginate_by = ITEMS_ON_PAGE
    permission_model = TaskModel
    template_name = "trackerapp/message_list.html"

    def get_queryset(self, **kwargs):
        message_list = Message.objects.filter(
            Q(task_id__exact=self.kwargs.get("pk")),
            Q(task__owner__exact=self.request.user)
            | Q(task__assignee__exact=self.request.user),
        ).order_by("creation_date")

        filtered_list = filters.MessageDateFilter(self.request.GET, queryset=message_list)
        return filtered_list.qs


class MessageCreate(LoginRequiredMixin, ExtendedCreateView):
    """
    Form to create message...
    """

    model = Message
    fields = [
        "body",
    ]

    # set owner and task relations for created message
    def form_valid(self, form, **kwargs):
        form.instance.owner = self.request.user
        form.instance.task = TaskModel.objects.get(
            Q(pk=self.kwargs.get("pk")), (Q(owner=self.request.user) | Q(assignee=self.request.user))
        )
        return super(MessageCreate, self).form_valid(form)


class MessageUpdate(IsOwnerPermissionRequiredMixin, ExtendedUpdateView):
    """
    Form to update comments
    """

    model = permission_model = Message
    fields = [
        "body",
    ]


class MessageDelete(IsOwnerPermissionRequiredMixin, ExtendedDeleteView):
    model = permission_model = Message

    def get_success_url(self):
        return reverse_lazy("comment-list", kwargs={"pk": self.object.task_id})


class MessageDetail(IsOwnerOrAssigneePermissionRequiredMixin, ExtendedDetailView):
    model = permission_model = Message


class AttachmentDetail(IsOwnerOrAssigneePermissionRequiredMixin, ExtendedDetailView):
    model = permission_model = Attachment


class AttachmentList(IsTaskOwnerOrAssignee, ExtendedFilterListView):
    model = Attachment
    permission_model = TaskModel
    filterset_class = filters.AttachmentDateFilter
    paginate_by = ITEMS_ON_PAGE
    template_name = "trackerapp/attachment_list.html"

    def get_queryset(self, **kwargs):
        attachment_list = Attachment.objects.filter(
            Q(task_id__exact=self.kwargs.get("pk")),
            Q(task__owner__exact=self.request.user)
            | Q(task__assignee__exact=self.request.user),
        ).order_by("creation_date")

        filtered_list = filters.AttachmentDateFilter(self.request.GET, queryset=attachment_list)
        return filtered_list.qs


class AttachmentCreate(LoginRequiredMixin, ExtendedCreateView):
    model = Attachment

    fields = [
        "description",
        "file",
    ]

    # set owner and task relations for created message
    def form_valid(self, form, **kwargs):
        form.instance.owner = self.request.user
        form.instance.task = TaskModel.objects.get(
            Q(pk=self.kwargs.get("pk")), (Q(owner=self.request.user) | Q(assignee=self.request.user))
        )
        return super(AttachmentCreate, self).form_valid(form)


class AttachmentUpdate(IsOwnerPermissionRequiredMixin, ExtendedUpdateView):
    model = permission_model = Attachment
    fields = ["description", "file"]


class AttachmentDelete(IsOwnerPermissionRequiredMixin, ExtendedDeleteView):
    model = permission_model = Attachment

    def get_success_url(self):
        return reverse_lazy("attach-list", kwargs={"pk": self.object.task_id})


class UserProfileDetail(LoginRequiredMixin, ExtendedDetailView):
    model = UserProfile
    queryset = UserProfile.objects.all()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object:
            return redirect(reverse_lazy("user-profile-create"))

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        profile = None
        try:
            profile = UserProfile.objects.get(owner_id=self.request.user.id)
        except UserProfile.DoesNotExist as e:
            logging.warning(str(e)+"User: {}".format(self.request.user))

        return profile


class UserProfileCreate(LoginRequiredMixin, ExtendedCreateView):
    model = UserProfile
    form_class = UserProfileEditionForm

    def get(self, request, *args, **kwargs):
        self.object = None
        try:
            self.object = self.model.objects.get(owner_id=request.user.id)
        except self.model.DoesNotExist:
            pass

        if self.object:
            return redirect(reverse_lazy("user-profile-update"))

        return super().get(request, *args, **kwargs)

    # set profile owner directly from request
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(UserProfileCreate, self).form_valid(form)


class UserProfileUpdate(LoginRequiredMixin, ExtendedUpdateView):
    permission_model = UserProfile
    template_name = "trackerapp/userprofile_form.html"
    queryset = UserProfile.objects.all()
    form_class = UserProfileEditionForm

    def get_success_url(self):
        return reverse_lazy("user-profile-detail")

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object:
            return redirect(reverse_lazy("user-profile-create"))

        return super().get(request, *args, **kwargs)

    def get_object(self, queryset=None):
        profile = None
        try:
            profile = UserProfile.objects.get(owner_id=self.request.user.id)
        except UserProfile.DoesNotExist as e:
            logging.exception("User: {}, asked for not existing profile\n{}".format(self.request.user, e))

        return profile

    # to init first_name/last_name fields (OneToOne field in updateview do not init by default)
    def get_initial(self):
        initial = super().get_initial()
        initial["first_name"] = self.object.owner.first_name
        initial["last_name"] = self.object.owner.last_name
        return initial


def sign_up(request):
    """
    Sign up new user
    """
    if request.method == "POST":
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect("index")
    else:
        form = UserSignUpForm()
    return render(request, "trackerapp/sign_up.html", {"form": form})


class TaskHistoryListView(IsTaskOwnerOrAssignee, ExtendedTaskHistoryListView):
    model = TaskModel
    permission_model = TaskModel
    paginate_by = ITEMS_ON_PAGE
    template_name = "trackerapp/task_history.html"
