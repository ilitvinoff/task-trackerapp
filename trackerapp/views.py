from django.db.models.query_utils import InvalidQuery
from django.http.response import Http404
from django.urls.base import reverse_lazy
from django.views import generic
from .models import TaskModel
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from .forms import TaskSortingForm
from django.views.generic.edit import FormMixin


class TaskListView(LoginRequiredMixin, FormMixin, generic.ListView):
    model = TaskModel
    form_class = TaskSortingForm
    paginate_by = 5

    def get_queryset(self):
        tasklist = TaskModel.objects.filter(
            owner__exact=self.request.user).order_by('creation_date')

        if self.request.method == 'POST':
            sorting_form = TaskSortingForm(self.request.POST)

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
        else:
            sorting_form = TaskSortingForm()

        return tasklist


class AssigneeTaskListView(LoginRequiredMixin, generic.ListView):
    model = TaskModel
    context_object_name = 'assigned_tasks'
    template_name = 'trackerapp/assigned_list.html'
    paginate_by = 5

    def get_queryset(self):
        return TaskModel.objects.filter(assignee__exact=self.request.user)


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    model = TaskModel


class TaskCreate(LoginRequiredMixin, CreateView):
    model = TaskModel
    fields = ['title', 'description', 'status', 'assignee']

    def get_success_url(self):
        return reverse_lazy('task-detail', args=(self.object.id,))

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(TaskCreate, self).form_valid(form)


class TaskUpdate(LoginRequiredMixin, UpdateView):
    model = TaskModel
    fields = ['title', 'description', 'status', 'assignee']

    def get_success_url(self):
        return reverse_lazy('task-detail', args=(self.object.id,))

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


class TaskStatusUpdate(LoginRequiredMixin, UpdateView):
    model = TaskModel
    fields = ['status', ]

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


class TaskDelete(LoginRequiredMixin, DeleteView):
    model = TaskModel
    success_url = reverse_lazy('tasks')

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
