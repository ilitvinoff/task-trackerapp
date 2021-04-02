from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls.base import reverse_lazy

from .filters import task_filter, date_filter
from .forms import (
    TaskSortingForm,
    DateSortingForm,
    UserProfileUpdateForm,
    UserSignUpForm,
)
from .models import TaskModel, Message, UserProfile, Attachment
from .permissions import (
    IsOwnerOrAssigneePermissionRequiredMixin,
    IsOwnerPermissionRequiredMixin,
    custom_permissions_dispatch,
)

from .profile_generics import (
    ProfileInFormListView,
    ProfileInDetailView,
    ProfileInCreateView,
    ProfileInUpdateView,
    ProfileInDeleteView,
)


class TaskListView(LoginRequiredMixin, ProfileInFormListView):
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


class AssigneeTaskListView(LoginRequiredMixin, ProfileInFormListView):
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


class TaskDetail(IsOwnerOrAssigneePermissionRequiredMixin, ProfileInDetailView):
    model = TaskModel

    # Be sure that current user trying to view his own comment...
    def dispatch(self, request, *args, **kwargs):
        return custom_permissions_dispatch(
            self,
            IsOwnerOrAssigneePermissionRequiredMixin,
            TaskModel,
            request,
            has_assignee=True,
            *args,
            **kwargs
        )


class TaskCreate(LoginRequiredMixin, ProfileInCreateView):
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
        return custom_permissions_dispatch(
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
        return custom_permissions_dispatch(self, IsOwnerOrAssigneePermissionRequiredMixin, TaskModel, request,
                                           has_assignee=True, *args, **kwargs)


class TaskDelete(IsOwnerPermissionRequiredMixin, ProfileInDeleteView):
    """
    Form to delete task
    """

    model = TaskModel
    success_url = reverse_lazy("index")

    # Be sure that current user trying to delete his own task
    def dispatch(self, request, *args, **kwargs):
        return custom_permissions_dispatch(
            self, IsOwnerPermissionRequiredMixin, TaskModel, request, *args, **kwargs
        )


class MessageListView(LoginRequiredMixin, ProfileInFormListView):
    model = Message
    form_class = DateSortingForm
    paginate_by = 5

    def get_queryset(self, **kwargs):
        message_list = Message.objects.filter(
            Q(task_id__exact=self.kwargs.get("pk")),
            Q(task__owner__exact=self.request.user)
            | Q(task__assignee__exact=self.request.user),
        ).order_by("creation_date")
        return date_filter(self, message_list)


class MessageCreate(LoginRequiredMixin, ProfileInCreateView):
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
        return custom_permissions_dispatch(
            self, IsOwnerPermissionRequiredMixin, Message, request, *args, **kwargs
        )


class MessageDelete(IsOwnerPermissionRequiredMixin, ProfileInDeleteView):
    model = Message

    # success_url = reverse_lazy("comment-list")

    def get_success_url(self):
        return reverse_lazy("comment-list", kwargs={"pk": self.object.task_id})

    # Be sure that current user trying to delete his own comment...
    def dispatch(self, request, *args, **kwargs):
        return custom_permissions_dispatch(
            self, IsOwnerPermissionRequiredMixin, Message, request, *args, **kwargs
        )


# TODO: Add to attach-list/comments-list link to relative task. Add list of comments and attachments to task detail
#  view. Add api functionality for userprofile,attachments.

class MessageDetail(IsOwnerOrAssigneePermissionRequiredMixin, ProfileInDetailView):
    model = Message

    # Be sure that current user trying to view his own comment...
    def dispatch(self, request, *args, **kwargs):
        return custom_permissions_dispatch(
            self,
            IsOwnerOrAssigneePermissionRequiredMixin,
            Message,
            request,
            has_assignee=True,
            *args,
            **kwargs
        )


class AttachmentDetail(IsOwnerOrAssigneePermissionRequiredMixin, ProfileInDetailView):
    model = Attachment

    # Be sure that current user trying to view his own comment...
    def dispatch(self, request, *args, **kwargs):
        return custom_permissions_dispatch(
            self,
            IsOwnerOrAssigneePermissionRequiredMixin,
            Attachment,
            request,
            has_assignee=True,
            *args,
            **kwargs
        )


class AttachmentList(LoginRequiredMixin, ProfileInFormListView):
    model = Attachment
    form_class = DateSortingForm
    paginate_by = 5

    def get_queryset(self, **kwargs):
        attachment_list = Attachment.objects.filter(
            Q(task_id__exact=self.kwargs.get("pk")),
            Q(task__owner__exact=self.request.user)
            | Q(task__assignee__exact=self.request.user),
        ).order_by("creation_date")
        return date_filter(self, attachment_list)


class AttachmentCreate(LoginRequiredMixin, ProfileInCreateView):
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


class AttachmentUpdate(IsOwnerPermissionRequiredMixin, ProfileInUpdateView):
    model = Attachment
    fields = ["description", "file"]

    # Be sure that current user trying to edit his own comment...
    def dispatch(self, request, *args, **kwargs):
        return custom_permissions_dispatch(
            self, IsOwnerPermissionRequiredMixin, Attachment, request, *args, **kwargs
        )


class AttachmentDelete(IsOwnerPermissionRequiredMixin, ProfileInDeleteView):
    model = Attachment

    def get_success_url(self):
        return reverse_lazy("attach-list", kwargs={"pk": self.object.task_id})

    # Be sure that current user trying to delete his own comment...
    def dispatch(self, request, *args, **kwargs):
        return custom_permissions_dispatch(
            self, IsOwnerPermissionRequiredMixin, Attachment, request, *args, **kwargs
        )


class UserProfileDetail(IsOwnerPermissionRequiredMixin, ProfileInDetailView):
    model = UserProfile
    queryset = UserProfile.objects.all()

    # Be sure that current user trying to view his own profile...
    def dispatch(self, request, *args, **kwargs):
        return custom_permissions_dispatch(
            self, IsOwnerPermissionRequiredMixin, UserProfile, request, *args, **kwargs
        )


class UserProfileUpdate(IsOwnerPermissionRequiredMixin, ProfileInUpdateView):
    template_name = "trackerapp/userprofile_form.html"
    queryset = UserProfile.objects.all()
    form_class = UserProfileUpdateForm

    def get_success_url(self):
        return reverse_lazy("user-profile-detail", args=(self.object.id,))

    # Be sure that current user trying to view his own profile...
    def dispatch(self, request, *args, **kwargs):
        return custom_permissions_dispatch(
            self, IsOwnerPermissionRequiredMixin, UserProfile, request, *args, **kwargs
        )

    def get_object(self, **kwargs):
        return UserProfile.objects.get(pk=self.kwargs["pk"])

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
