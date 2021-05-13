import os

from diff_match_patch import diff_match_patch
from django.views import generic
from django_filters.views import FilterView

from trackerapp.models import UserProfile, Message, TaskModel, Attachment

ITEMS_ON_PAGE = 5


def add_extra_context(user_id, context_data):
    try:
        context_data["userprofile_id"] = UserProfile.objects.get(owner_id=user_id).id  # add extra context
    except UserProfile.DoesNotExist:
        context_data["userprofile_id"] = None
    return context_data


class ExtendedFilterListView(FilterView):  # pylint: disable=too-many-ancestors
    """
    Pra-class to may create form in list view.
    Overriding get and post methods. Extended with extra context
    in overridden get_context_data method.
    """

    # add extra-context and task-related to message/attachment list
    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)  # get the default context data
        try:
            context_data['related_task_id'] = self.kwargs['pk']
        except:
            pass
        return add_extra_context(self.request.user.id, context_data)


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
    """
    To view list of related obj on detail view page of master obj
    """
    paginate_by = ITEMS_ON_PAGE
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
    """
    To view list of events in history for task and related to it attachments
    """
    VALUE_MARKER = "-1"  # mark history instance when it's the earliest exemplar

    def get_queryset(self, **kwargs):
        """
        Here form queryset, which consists of the task's history and
        of the related to the task attachment's history
        """
        history_list = []
        task = TaskModel.objects.filter(id=self.kwargs['pk']).first()
        attachments = Attachment.objects.filter(task=task)

        for attachment in attachments:
            history_list.extend(attachment.history.all())

        if task:
            history_list.extend(task.history.all())

        history_list.sort(key=lambda a: a.history_date, reverse=True)
        return history_list

    def get_context_data(self, **kwargs):
        """
        Here form event list, which consists of the task's history and
        of the related to the task attachment's history, ordered by history date and
        put it to context_data
        """
        context_data = super().get_context_data(**kwargs)  # get the default context data
        try:
            context_data['related_task_id'] = self.kwargs['pk']
            context_data['related_task_title'] = TaskModel.objects.get(id=self.kwargs['pk']).title
        except:
            pass

        event_list = []
        for item in context_data['object_list']:

            model_name = 'task' if item.instance_type == TaskModel else 'attachment "{}"'.format(
                os.path.split(item.instance.file.name)[1])

            if item.prev_record is None:
                result = {'model_name': model_name, 'datetime': item.creation_date, 'changed_by': item.owner,
                          'changes': [{'field': '', 'value': self.VALUE_MARKER}]}

            else:
                delta = item.diff_against(item.prev_record)
                result = {'model_name': model_name, 'datetime': item.history_date, 'changed_by': item.history_user,
                          'changes': []}

                for change in delta.changes:
                    result['changes'].append({'field': str(change.field),
                                              'value': diff_semantic(str(change.old), str(change.new)),
                                              })

            event_list.append(result)

        context_data['event_list'] = event_list

        return add_extra_context(self.request.user.id, context_data)
