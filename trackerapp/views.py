from django.http.response import Http404
from django.urls.base import reverse_lazy
from django.utils.translation import ugettext as _
from django.views import generic
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormMixin
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.auth.forms import UserCreationForm
from .models import TaskModel, Message
from .forms import TaskSortingForm, MessageSortingForm


class FormListView(FormMixin, generic.ListView):  # pylint: disable=too-many-ancestors
    """
    Pra-class to may create form in list view.
    Overriding get and post methods.
    """

    def get(self, request, *args, **kwargs):
        # From FormMixin
        form_class = self.get_form_class()
        self.form = self.get_form(form_class)

        # From ListView
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(
                _(u"Empty list and '%(class_name)s.allow_empty' is False.")
                % {"class_name": self.__class__.__name__}
            )

        context = self.get_context_data(
            object_list=self.object_list, form=self.form)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


def task_filter(obj, tasklist):
    """
    task_filter - to filter list of task by values from form
    """
    if obj.request.method == "POST":
        sorting_form = TaskSortingForm(obj.request.POST)

        if sorting_form.is_valid():
            date_from = sorting_form.cleaned_data["from_date"]
            date_till = sorting_form.cleaned_data["till_date"]
            choose_status = sorting_form.cleaned_data["choose_status"]

            if date_from:
                tasklist = tasklist.filter(creation_date__gte=date_from)

            if date_till:
                tasklist = tasklist.filter(creation_date__lte=date_till)

            if choose_status:
                tasklist = tasklist.filter(status__exact=choose_status)
        else:
            TaskSortingForm()
    return tasklist


class TaskListView(LoginRequiredMixin, FormListView):  # pylint: disable=too-many-ancestors
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


class AssigneeTaskListView(LoginRequiredMixin, FormListView):  # pylint: disable=too-many-ancestors
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


class TaskCreate(LoginRequiredMixin, CreateView):
    """
    Form to create task.
    """
    model = TaskModel
    fields = ["title", "description", "status", "assignee"]

    # after successful creation redirects to the created task page
    def get_success_url(self):
        return reverse_lazy("task-detail", args=(self.object.id,))

    # override form_valid, to save owner(creator) of the task
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(TaskCreate, self).form_valid(form)


class TaskUpdate(LoginRequiredMixin, UpdateView):
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
        # Take pk from kwargs
        pk = kwargs.get("pk")  # example
        # Take user from request
        user = request.user
        # check permission
        try:
            TaskModel.objects.get(pk=pk, owner=user)
            return super(TaskUpdate, self).dispatch(request, *args, **kwargs)
        except TaskModel.DoesNotExist as try_update_not_owned_task:
            raise PermissionDenied() from try_update_not_owned_task


class TaskStatusUpdate(LoginRequiredMixin, UpdateView):
    """
    Form to edit task status (for assignee...)
    """
    model = TaskModel
    fields = [
        "status",
    ]

    # Be sure that current user trying to edit status of the task assigned to him
    def dispatch(self, request, *args, **kwargs):
        # Take pk from kwargs
        pk = kwargs.get("pk")  # example
        # Take user from request
        user = request.user
        # check permission
        try:
            task = TaskModel.objects.get(pk=pk)

            if user == task.assignee or user == task.owner:
                return super(TaskStatusUpdate, self).dispatch(request, *args, **kwargs)
            raise PermissionDenied()

        except TaskModel.DoesNotExist as try_update_not_owned_task:
            raise Http404() from try_update_not_owned_task


class TaskDelete(LoginRequiredMixin, DeleteView):
    """
    Form to delete task
    """
    model = TaskModel
    success_url = reverse_lazy("tasks")

    # Be sure that current user trying to delete his own task
    def dispatch(self, request, *args, **kwargs):
        # Take pk from kwargs:
        pk = kwargs.get("pk")  # example
        # Take user from request
        user = request.user
        # check permission
        try:
            TaskModel.objects.get(pk=pk, owner=user)
            return super(TaskDelete, self).dispatch(request, *args, **kwargs)
        except TaskModel.DoesNotExist as try_delete_not_owned_task:
            raise PermissionDenied() from try_delete_not_owned_task


def message_filter(obj, message_list):
    """
    message_filter - to filter list of messages by values from form
    """
    if obj.request.method == "POST":
        sorting_form = MessageSortingForm(obj.request.POST)

        if sorting_form.is_valid():
            date_from = sorting_form.cleaned_data["from_date"]
            date_till = sorting_form.cleaned_data["till_date"]

            if date_from:
                message_list = message_list.filter(creation_date__gte=date_from)

            if date_till:
                message_list = message_list.filter(creation_date__lte=date_till)

        else:
            MessageSortingForm()
    return message_list


class MessageListView(LoginRequiredMixin, FormListView):
    model = Message
    form_class = MessageSortingForm
    paginate_by = 5

    def get_queryset(self):
        message_list = Message.objects.filter(owner__exact=self.request.user).order_by(
            "creation_date")
        return message_filter(self, message_list)


@login_required
def task_detail(request, pk):
    """
    To view task details
    """
    try:
        task = TaskModel.objects.get(pk=pk)
    except ObjectDoesNotExist as task_does_not_exist:
        raise Http404 from task_does_not_exist

    user = request.user
    if user == task.owner or user == task.assignee:
        return render(
            request, "trackerapp/taskmodel_detail.html", context={"taskmodel": task}
        )
    raise PermissionDenied()


def sign_up(request):
    """
    Sign up new user
    """
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect("/")
    else:
        form = UserCreationForm()
    return render(request, "trackerapp/sign_up.html", {"form": form})
