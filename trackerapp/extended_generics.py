from diff_match_patch import diff_match_patch
from django.http.response import Http404
from django.utils.translation import ugettext as _
from django.views import generic
from django.views.generic.edit import FormMixin

from trackerapp.models import UserProfile, Message, TaskModel


def add_extra_context(user_id, context_data):
    try:
        context_data["userprofile_id"] = UserProfile.objects.get(owner_id=user_id).id  # add extra context
    except UserProfile.DoesNotExist:
        context_data["userprofile_id"] = None
    return context_data


class ExtendedFormListView(FormMixin, generic.ListView):  # pylint: disable=too-many-ancestors
    """
    Pra-class to may create form in list view.
    Overriding get and post methods, extended with extra context
    in overridden get_context_date method.
    """

    # add extra-context and task-related to message/attachment list
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)  # get the default context data
        try:
            context_data['related_task_id'] = self.kwargs['pk']
        except:
            pass
        return add_extra_context(self.request.user.id, context_data)

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

        context = self.get_context_data(object_list=self.object_list, form=self.form)
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


class ExtendedDetailView(generic.DetailView):
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)  # get the default context data
        return add_extra_context(self.request.user.id, context_data)


class ExtendedUpdateView(generic.UpdateView):
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)  # get the default context data
        return add_extra_context(self.request.user.id, context_data)


class ExtendedCreateView(generic.CreateView):
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)  # get the default context data
        return add_extra_context(self.request.user.id, context_data)


class ExtendedDeleteView(generic.DeleteView):
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)  # get the default context data
        return add_extra_context(self.request.user.id, context_data)


class ListInDetailView(ExtendedDetailView, generic.list.MultipleObjectMixin):
    paginate_by = 5
    defaultModel = Message

    def get_context_data(self, **kwargs):
        object_list = self.defaultModel.objects.filter(task=self.get_object())
        context_data = super().get_context_data(object_list=object_list, **kwargs)
        return add_extra_context(self.request.user.id, context_data)


def diff_semantic(text1, text2):
    dmp = diff_match_patch()
    d = dmp.diff_main(text1, text2)
    dmp.diff_cleanupSemantic(d)
    return d


class ExtendedTaskHistoryListView(generic.ListView):

    def get_queryset(self, **kwargs):
        task = TaskModel.objects.filter(id=self.kwargs['pk']).first()
        history_list = []
        if task:
            history_list = task.history.all().order_by("-history_date")
        return history_list

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)  # get the default context data
        try:
            context_data['related_task_id'] = self.kwargs['pk']
            context_data['related_task_title'] = TaskModel.objects.get(id=self.kwargs['pk']).title
        except:
            pass

        event_list = []
        for item in context_data['object_list']:

            try:
                previous_item_state = item.get_previous_by_history_date()
            except:
                previous_item_state = None

            if previous_item_state is None:
                context_data['event_list'] = [
                    [{'field': 'Task created', 'datetime': item.creation_date, 'changed_by': item.owner}], ]

            else:
                delta = item.diff_against(previous_item_state)
                result = {'datetime': item.history_date, 'changed_by': item.history_user, 'changes': []}
                for change in delta.changes:
                    result['changes'].append({'field': str(change.field),
                                              'value': diff_semantic(str(change.old), str(change.new)),
                                              })

                event_list.append(result)

            context_data['event_list'] = event_list

        return add_extra_context(self.request.user.id, context_data)
