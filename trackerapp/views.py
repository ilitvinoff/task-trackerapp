from django.db.models.query_utils import InvalidQuery
from django.http.response import Http404
from django.urls.base import reverse_lazy
from django.views import generic
from .models import TaskModel
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormMixin
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from .forms import TaskSortingForm
from django.utils.translation import ugettext as _


"""
Pra-class to may create form in list view.
Overriding get and post methods.
"""


class FormListView(FormMixin, generic.ListView):
    def get(self, request, *args, **kwargs):
        # From FormMixin
        form_class = self.get_form_class()
        self.form = self.get_form(form_class)

        # From ListView
        self.object_list = self.get_queryset()
        allow_empty = self.get_allow_empty()
        if not allow_empty and len(self.object_list) == 0:
            raise Http404(_(u"Empty list and '%(class_name)s.allow_empty' is False.")
                          % {'class_name': self.__class__.__name__})

        context = self.get_context_data(
            object_list=self.object_list, form=self.form)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


""" 
task_filter - to filter list of task by values from form
"""


def task_filter(obj, tasklist):
    if obj.request.method == 'POST':
        sorting_form = TaskSortingForm(obj.request.POST)

        if sorting_form.is_valid():
            date_from = sorting_form.cleaned_data['from_date']
            date_till = sorting_form.cleaned_data['till_date']
            choose_status = sorting_form.cleaned_data['choose_status']

            if date_from:
                tasklist = tasklist.filter(creation_date__gte=date_from)

            if date_till:
                tasklist = tasklist.filter(creation_date__lte=date_till)

            if choose_status:
                tasklist = tasklist.filter(status__exact=choose_status)
        else:
            raise InvalidQuery()
    return tasklist


""" 
ListView of created by user tasks, contains form to filter tasks
"""


class TaskListView(LoginRequiredMixin, FormListView):
    model = TaskModel
    form_class = TaskSortingForm
    paginate_by = 5

    def get_queryset(self):
        tasklist = TaskModel.objects.filter(
            owner__exact=self.request.user).order_by('creation_date')
        return task_filter(self, tasklist)


""" 
ListView of assigned to user tasks, contains form to filter tasks
"""


class AssigneeTaskListView(LoginRequiredMixin, FormListView):
    model = TaskModel
    form_class = TaskSortingForm
    context_object_name = 'assigned_tasks'
    template_name = 'trackerapp/assigned_list.html'
    paginate_by = 5

    def get_queryset(self):
        tasklist = TaskModel.objects.filter(assignee__exact=self.request.user)
        return task_filter(self, tasklist)


"""
Form to create task.
"""


class TaskCreate(LoginRequiredMixin, CreateView):
    model = TaskModel
    fields = ['title', 'description', 'status', 'assignee']

    # after successful creation redirects to the created task page
    def get_success_url(self):
        return reverse_lazy('task-detail', args=(self.object.id,))

    # override form_valid, to save owner(creator) of the task
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(TaskCreate, self).form_valid(form)


"""
Edit task form
"""


class TaskUpdate(LoginRequiredMixin, UpdateView):
    model = TaskModel
    fields = ['title', 'description', 'status', 'assignee']

    # after successful edition redirects to the edited task page
    def get_success_url(self):
        return reverse_lazy('task-detail', args=(self.object.id,))

    # Be sure that current user trying to edit his own task...
    def dispatch(self, request, *args, **kwargs):
        # Take pk from kwargs
        pk = kwargs.get('pk')  # example
        # Take user from request
        user = request.user
        # check permission
        try:
            TaskModel.objects.get(pk=pk, owner=user)
            return super(TaskUpdate, self).dispatch(request, *args, **kwargs)
        except TaskModel.DoesNotExist:
            raise PermissionDenied()


"""
Form to edit task status (for assignee...)
"""


class TaskStatusUpdate(LoginRequiredMixin, UpdateView):
    model = TaskModel
    fields = ['status', ]

    # Be sure that current user trying to edit status of the task assigned to him
    def dispatch(self, request, *args, **kwargs):
        # Take pk from kwargs
        pk = kwargs.get('pk')  # example
        # Take user from request
        user = request.user
        # check permission
        try:
            task = TaskModel.objects.get(pk=pk)
            if user in task.assignee.all():
                return super(TaskStatusUpdate, self).dispatch(request, *args, **kwargs)
            else:
                raise PermissionDenied()
        except TaskModel.DoesNotExist:
            raise Http404()


"""
Form to delete task
"""


class TaskDelete(LoginRequiredMixin, DeleteView):
    model = TaskModel
    success_url = reverse_lazy('tasks')

    # Be sure that current user trying to delete his own task
    def dispatch(self, request, *args, **kwargs):
        # Take pk from kwargs
        pk = kwargs.get('pk')  # example
        # Take user from request
        user = request.user
        # check permission
        try:
            TaskModel.objects.get(pk=pk, owner=user)
            return super(TaskDelete, self).dispatch(request, *args, **kwargs)
        except TaskModel.DoesNotExist:
            raise PermissionDenied()


"""
To view task details
"""


@login_required
def task_detail(request, pk):
    try:
        task = TaskModel.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise Http404

    user = request.user
    if user == task.owner or user in task.assignee.all():
        return render(request, 'trackerapp/taskmodel_detail.html', context={'taskmodel': task})
    raise PermissionDenied()


"""
Sign up new user
"""


def sign_up(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'trackerapp/sign_up.html', {'form': form})
