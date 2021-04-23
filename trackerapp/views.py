from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls.base import reverse_lazy

from .extended_generics import (
    ExtendedFormListView,
    ExtendedDetailView,
    ExtendedCreateView,
    ExtendedUpdateView,
    ExtendedDeleteView,
    ListInDetailView,
)
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
)

ITEMS_ON_PAGE = 5


class TaskListView(LoginRequiredMixin, ExtendedFormListView):
    """
    ListView of created by user tasks, contains form to filter tasks
    """

    model = TaskModel
    form_class = TaskSortingForm
    paginate_by = ITEMS_ON_PAGE

    def get_queryset(self):
        tasklist = TaskModel.objects.filter(owner=self.request.user).order_by("creation_date")
        return task_filter(self, tasklist)


class AssigneeTaskListView(LoginRequiredMixin, ExtendedFormListView):
    """
    ListView of assigned to user tasks, contains form to filter tasks
    """

    model = TaskModel
    form_class = TaskSortingForm
    context_object_name = "assigned_tasks"
    template_name = "trackerapp/assigned_list.html"
    paginate_by = ITEMS_ON_PAGE

    def get_queryset(self):
        tasklist = TaskModel.objects.filter(assignee=self.request.user)
        return task_filter(self, tasklist)


class TaskDetail(IsOwnerOrAssigneePermissionRequiredMixin, ListInDetailView):
    model = permission_class_model = TaskModel
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

    model = permission_class_model = TaskModel
    fields = ["title", "description", "status", "assignee"]

    # after successful edition redirects to the edited task page
    def get_success_url(self):
        return reverse_lazy("task-detail", args=(self.object.id,))


class TaskStatusUpdate(IsOwnerOrAssigneePermissionRequiredMixin, ExtendedUpdateView):
    """
    Form to edit task status (for assignee...)
    """

    model = permission_class_model = TaskModel
    fields = [
        "status",
    ]


class TaskDelete(IsOwnerPermissionRequiredMixin, ExtendedDeleteView):
    """
    Form to delete task
    """

    model = permission_class_model = TaskModel
    success_url = reverse_lazy("index")


class MessageListView(IsOwnerOrAssigneePermissionRequiredMixin, ExtendedFormListView):
    model = Message
    form_class = DateSortingForm
    paginate_by = ITEMS_ON_PAGE
    permission_class_model = TaskModel
    has_assignee = True

    def get_queryset(self, **kwargs):
        message_list = Message.objects.filter(
            Q(task_id__exact=self.kwargs.get("pk")),
            Q(task__owner__exact=self.request.user)
            | Q(task__assignee__exact=self.request.user),
        ).order_by("creation_date")
        return date_filter(self, message_list)


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

    model = permission_class_model = Message
    fields = [
        "body",
    ]


class MessageDelete(IsOwnerPermissionRequiredMixin, ExtendedDeleteView):
    model = permission_class_model = Message

    def get_success_url(self):
        return reverse_lazy("comment-list", kwargs={"pk": self.object.task_id})


class MessageDetail(IsOwnerOrAssigneePermissionRequiredMixin, ExtendedDetailView):
    model = permission_class_model = Message


class AttachmentDetail(IsOwnerOrAssigneePermissionRequiredMixin, ExtendedDetailView):
    model = permission_class_model = Attachment


class AttachmentList(IsOwnerOrAssigneePermissionRequiredMixin, ExtendedFormListView):
    model = Attachment
    permission_class_model = TaskModel
    form_class = DateSortingForm
    paginate_by = ITEMS_ON_PAGE

    def get_queryset(self, **kwargs):
        attachment_list = Attachment.objects.filter(
            Q(task_id__exact=self.kwargs.get("pk")),
            Q(task__owner__exact=self.request.user)
            | Q(task__assignee__exact=self.request.user),
        ).order_by("creation_date")
        return date_filter(self, attachment_list)


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
    model = permission_class_model = Attachment
    fields = ["description", "file"]


class AttachmentDelete(IsOwnerPermissionRequiredMixin, ExtendedDeleteView):
    model = permission_class_model = Attachment

    def get_success_url(self):
        return reverse_lazy("attach-list", kwargs={"pk": self.object.task_id})


class UserProfileDetail(IsOwnerPermissionRequiredMixin, ExtendedDetailView):
    model = permission_class_model = UserProfile
    queryset = UserProfile.objects.all()


class UserProfileUpdate(IsOwnerPermissionRequiredMixin, ExtendedUpdateView):
    permission_class_model = UserProfile
    template_name = "trackerapp/userprofile_form.html"
    queryset = UserProfile.objects.all()
    form_class = UserProfileUpdateForm

    def get_success_url(self):
        return reverse_lazy("user-profile-detail", args=(self.object.id,))

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


class TaskHistoryListView(IsOwnerOrAssigneePermissionRequiredMixin, ExtendedFormListView):
    model = TaskModel
    permission_class_model = TaskModel
    form_class = DateSortingForm
    paginate_by = ITEMS_ON_PAGE
    template_name = "trackerapp/task_history.html"

    def get_context_data(self, **kwargs):
        context_data = super(TaskHistoryListView, self).get_context_data()
        events_list = []
        for item in context_data['object_list']:
            previous_item_state = item.get_previous_by_history_date()
            delta = item.diff_against(previous_item_state)
            # TODO add changes to context as diff_match_patch
            for change in delta.changes:
                events_list.append((change.field,))
        return context_data

        return context_data

    def get_queryset(self, **kwargs):
        history_list = TaskModel.history.filter(id=self.kwargs['pk']).order_by("-history_date")
        return date_filter(self, history_list)
