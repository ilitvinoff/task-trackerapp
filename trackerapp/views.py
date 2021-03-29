from django.db.models import Q
from django.urls.base import reverse_lazy
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.contrib.auth.forms import UserCreationForm
from .filters import task_filter, message_filter
from .models import TaskModel, Message, UserProfile
from .forms import TaskSortingForm, MessageSortingForm, UserProfileForm, UserSignUpForm
from .permissions import (
    IsOwnerOrAssigneePermissionRequiredMixin,
    IsOwnerPermissionRequiredMixin,
    dispatch_override,
)

from .profile_generics import FormListView, ProfileDetailInView, ProfileInCreateView, ProfileInUpdateView, \
    ProfileInDeleteView, ProfileInFormView


class TaskListView(
    LoginRequiredMixin, FormListView
):  # pylint: disable=too-many-ancestors
    """
    ListView of created by user tasks, contains form to filter tasks
    """

    model = TaskModel
    form_class = TaskSortingForm
    paginate_by = 5

    def get_queryset(self):
        tasklist = TaskModel.objects.filter(owner__exact=self.request.user).order_by(
            "creation_date"
        )
        return task_filter(self, tasklist)


class AssigneeTaskListView(
    LoginRequiredMixin, FormListView
):  # pylint: disable=too-many-ancestors
    """
    ListView of assigned to user tasks, contains form to filter tasks
    """

    model = TaskModel
    form_class = TaskSortingForm
    context_object_name = "assigned_tasks"
    template_name = "trackerapp/assigned_list.html"
    paginate_by = 5

    def get_queryset(self):
        tasklist = TaskModel.objects.filter(assignee__exact=self.request.user)
        return task_filter(self, tasklist)


class TaskDetail(IsOwnerOrAssigneePermissionRequiredMixin, ProfileDetailInView):
    model = TaskModel

    # Be sure that current user trying to view his own comment...
    def dispatch(self, request, *args, **kwargs):
        return dispatch_override(
            self, IsOwnerOrAssigneePermissionRequiredMixin, TaskModel, request, has_assignee=True, *args, **kwargs
        )


class TaskCreate(LoginRequiredMixin, ProfileInCreateView):
    """
    Form to create task.
    """

    model = TaskModel
    fields = ["title", "description", "status", "assignee"]

    # override form_valid, to save owner(creator) of the task
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(TaskCreate, self).form_valid(form)


class TaskUpdate(IsOwnerPermissionRequiredMixin, ProfileInUpdateView):
    """
    Edit task form
    """

    model = TaskModel
    fields = ["title", "description", "status", "assignee"]

    # after successful edition redirects to the edited task page
    def get_success_url(self):
        return reverse_lazy("task-detail", args=(self.object.id,))

    # Be sure that current user trying to edit his own task...
    def dispatch(self, request, *args, **kwargs):
        return dispatch_override(
            self, IsOwnerPermissionRequiredMixin, TaskModel, request, *args, **kwargs
        )


class TaskStatusUpdate(IsOwnerOrAssigneePermissionRequiredMixin, ProfileInUpdateView):
    """
    Form to edit task status (for assignee...)
    """

    model = TaskModel
    fields = [
        "status",
    ]

    # Be sure that current user trying to edit status of the task assigned to him
    def dispatch(self, request, *args, **kwargs):
        return dispatch_override(self, IsOwnerOrAssigneePermissionRequiredMixin, TaskModel, request, has_assignee=True,
                                 *args, **kwargs)


class TaskDelete(IsOwnerPermissionRequiredMixin, ProfileInDeleteView):
    """
    Form to delete task
    """

    model = TaskModel
    success_url = reverse_lazy("tasks")

    # Be sure that current user trying to delete his own task
    def dispatch(self, request, *args, **kwargs):
        return dispatch_override(
            self, IsOwnerPermissionRequiredMixin, TaskModel, request, *args, **kwargs
        )


class MessageListView(LoginRequiredMixin, FormListView):
    model = Message
    form_class = MessageSortingForm
    paginate_by = 5

    def get_queryset(self, **kwargs):
        message_list = Message.objects.filter(
            Q(task_id__exact=self.kwargs.get("pk")),
            Q(task__owner__exact=self.request.user)
            | Q(task__assignee__exact=self.request.user),
        ).order_by("creation_date")
        return message_filter(self, message_list)


class MessageCreate(LoginRequiredMixin, ProfileInCreateView):
    """
    Form to create message...
    """

    model = Message
    fields = [
        "body",
    ]

    # after successful creation redirects to the created task page
    # def get_success_url(self):
    #     return reverse_lazy("message-detail", args=(self.object.id,))

    def form_valid(self, form, **kwargs):
        form.instance.owner = self.request.user
        form.instance.task = TaskModel.objects.get(pk=self.kwargs.get("pk"))
        return super(MessageCreate, self).form_valid(form)

    # after successful creation redirects to the relatives task page
    # def get_success_url(self, **kwargs):
    #     message = Message.objects.filter(task__pk=self.kwargs.get("pk"))
    #     return reverse_lazy("comment-list")


class MessageUpdate(IsOwnerPermissionRequiredMixin, ProfileInUpdateView):
    """
    Form to update comments
    """

    model = Message
    fields = [
        "body",
    ]

    # Be sure that current user trying to edit his own comment...
    def dispatch(self, request, *args, **kwargs):
        return dispatch_override(
            self, IsOwnerPermissionRequiredMixin, Message, request, *args, **kwargs
        )


class MessageDelete(IsOwnerPermissionRequiredMixin, ProfileInDeleteView):
    model = Message
    success_url = reverse_lazy("comment-list")

    # Be sure that current user trying to delete his own comment...
    def dispatch(self, request, *args, **kwargs):
        return dispatch_override(
            self, IsOwnerPermissionRequiredMixin, Message, request, *args, **kwargs
        )


class MessageDetail(IsOwnerOrAssigneePermissionRequiredMixin, ProfileDetailInView):
    model = Message

    # Be sure that current user trying to view his own comment...
    def dispatch(self, request, *args, **kwargs):
        return dispatch_override(
            self, IsOwnerOrAssigneePermissionRequiredMixin, Message, request, has_assignee=True, *args, **kwargs
        )


class UserProfileDetail(IsOwnerPermissionRequiredMixin, ProfileDetailInView):
    model = UserProfile
    queryset = UserProfile.objects.all()

    # Be sure that current user trying to view his own profile...
    def dispatch(self, request, *args, **kwargs):
        return dispatch_override(
            self, IsOwnerPermissionRequiredMixin, UserProfile, request, *args, **kwargs
        )


class UserProfileUpdate(IsOwnerPermissionRequiredMixin, ProfileInUpdateView):
    template_name = 'trackerapp/userprofile_form.html'
    queryset = UserProfile.objects.all()
    form_class = UserProfileForm

    def get_success_url(self):
        return reverse_lazy("user-profile-detail", args=(self.object.id,))

    # Be sure that current user trying to view his own profile...
    def dispatch(self, request, *args, **kwargs):
        return dispatch_override(
            self, IsOwnerPermissionRequiredMixin, UserProfile, request, *args, **kwargs)


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
            return redirect("/")
    else:
        form = UserSignUpForm()
    return render(request, "trackerapp/sign_up.html", {"form": form})
