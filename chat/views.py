# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy

from chat.filter import room_list_filter
from chat.forms import RoomSortingForm
from chat.models import ChatRoomModel, ChatMessageModel
from trackerapp.extended_generics import ExtendedCreateView, ExtendedFormListView, ExtendedDeleteView, \
    ExtendedUpdateView
from trackerapp.models import UserProfile
from trackerapp.permissions import IsOwnerPermissionRequiredMixin

ITEMS_ON_PAGE = 10
HISTORY_MESSAGE_COUNT = 100


def room_detail(request, pk):
    """
    Detail room's view
    """
    user = request.user
    room = ChatRoomModel.objects.filter(pk=pk).first()
    room_name = None

    try:
        room_name = ChatRoomModel.objects.get(id=pk).name
    except:
        pass

    if not room and room.is_private and not (room.get_owner() == user or user in room.member.all()):
        raise PermissionDenied("Permission denied. You have no permission to act with this room")

    userprofile_id = UserProfile.objects.get(owner_id=user.id).id

    message_history_list = ChatMessageModel.objects.filter(room=room).order_by('creation_date')[
                           :HISTORY_MESSAGE_COUNT]

    extra_data = {
        'pk': pk, 'room_name': room_name,
        'userprofile_id': userprofile_id,
        'message_history': message_history_list,
    }

    return render(request, 'room.html', extra_data)


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


class ListChatRoomView(LoginRequiredMixin, ExtendedFormListView):
    model = ChatRoomModel
    form_class = RoomSortingForm
    paginate_by = ITEMS_ON_PAGE
    template_name = "chat/room_list.html"

    def get_queryset(self):
        room_list = ChatRoomModel.objects.filter(
            Q(is_private=False) | Q(Q(is_private=True),
                                    Q(Q(member=self.request.user) | Q(owner=self.request.user))))
        return room_list_filter(self, room_list)


class DeleteChatRoomView(IsOwnerPermissionRequiredMixin, ExtendedDeleteView):
    model = permission_class_model = ChatRoomModel
    success_url = reverse_lazy("room-list")
    template_name = "chat/room_confirm_delete.html"


class UpdateChatRoomView(IsOwnerPermissionRequiredMixin, ExtendedUpdateView):
    model = permission_class_model = ChatRoomModel
    fields = ["member", "name", "is_private"]
    template_name = "chat/room_form.html"
