# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy

from chat.models import ChatRoomModel, ChatMessageModel
from trackerapp.extended_generics import (
    ExtendedCreateView, ExtendedFilterListView, ExtendedDeleteView, ExtendedUpdateView, ExtendedDetailView
)
from trackerapp.filters import ChatRoomFilter
from trackerapp.permissions import IsOwnerPermissionRequiredMixin, ChatRoomPermission

ITEMS_ON_PAGE = 5
HISTORY_MESSAGE_COUNT = 100


class ChatRoomDetail(ChatRoomPermission, ExtendedDetailView):
    model = permission_model = ChatRoomModel
    template_name = "room.html"

    def get_context_data(self, **kwargs):
        context_data = super(ChatRoomDetail, self).get_context_data()

        message_history_list = ChatMessageModel.objects.filter(room=self.object).order_by('creation_date')[
                               :HISTORY_MESSAGE_COUNT]
        extra_data = {
            'message_history': message_history_list,
        }

        context_data.update(extra_data)
        return context_data


class CreateChatRoomView(LoginRequiredMixin, ExtendedCreateView):
    model = ChatRoomModel
    fields = [
        "name",
        "is_private",
        "member",
    ]
    template_name = "chat/room_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(CreateChatRoomView, self).form_valid(form)


class ListChatRoomView(LoginRequiredMixin, ExtendedFilterListView):
    model = ChatRoomModel
    # form_class = RoomSortingForm
    paginate_by = ITEMS_ON_PAGE
    template_name = "chat/room_list.html"
    filterset_class = ChatRoomFilter

    def get_queryset(self):
        room_list = ChatRoomModel.objects.filter(Q(is_private=False) | Q(Q(is_private=True),
                                                                         Q(Q(member=self.request.user) | Q(
                                                                             owner=self.request.user)))).distinct()

        filtered_list = ChatRoomFilter(self.request.GET, queryset=room_list)
        return filtered_list.qs


class DeleteChatRoomView(IsOwnerPermissionRequiredMixin, ExtendedDeleteView):
    model = permission_model = ChatRoomModel
    success_url = reverse_lazy("room-list")
    template_name = "chat/room_confirm_delete.html"


class UpdateChatRoomView(IsOwnerPermissionRequiredMixin, ExtendedUpdateView):
    model = permission_model = ChatRoomModel
    fields = ["member", "name", "is_private"]
    template_name = "chat/room_form.html"
