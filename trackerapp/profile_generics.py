from django.http.response import Http404
from django.utils.translation import ugettext as _
from django.views import generic
from django.views.generic.edit import FormMixin

from trackerapp.models import UserProfile


def add_userprofile(user_id, context):
    try:
        context["userprofile"] = UserProfile.objects.get(owner_id=user_id)  # add extra context
    except UserProfile.DoesNotExist as e:
        context["userprofile"] = None
    return context


class FormListView(FormMixin, generic.ListView):  # pylint: disable=too-many-ancestors
    """
    Pra-class to may create form in list view.
    Overriding get and post methods.
    """

    def get_context_data(self, **kwargs):
        context = super(FormListView, self).get_context_data(**kwargs)  # get the default context data
        return add_userprofile(self.request.user.id, context)

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


class ProfileDetailInView(generic.DetailView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # get the default context data
        return add_userprofile(self.request.user.id, context)


class ProfileInUpdateView(generic.UpdateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # get the default context data
        return add_userprofile(self.request.user.id, context)


class ProfileInCreateView(generic.CreateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # get the default context data
        return add_userprofile(self.request.user.id, context)


class ProfileInDeleteView(generic.DeleteView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # get the default context data
        return add_userprofile(self.request.user.id, context)
