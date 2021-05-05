# Create your views here.
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse_lazy

from chat.models import ChatRoomModel
from trackerapp.extended_generics import ExtendedCreateView
from trackerapp.models import UserProfile


def index(request):
    userprofile_id = UserProfile.objects.get(owner_id=request.user.id).id
    return render(request, 'chat/index.html', context={'userprofile_id': userprofile_id})


def room(request, room_name):
    user = request.user
    room = ChatRoomModel.objects.filter(name=room_name).first()
    if not room or not (room.get_owner() == user or user in room.member.all()):
        raise PermissionDenied("Permission denied. You have no permission to this room")
    userprofile_id = UserProfile.objects.get(owner_id=user.id).id
    return render(request, 'room.html', {
        'room_name': room_name, 'userprofile_id': userprofile_id
    })


class CreateChatRoomView(LoginRequiredMixin, ExtendedCreateView):
    model = ChatRoomModel
    fields = [
        "name",
        "is_private",
        "member",
    ]
    template_name = "chat/room_form.html"

    def get_success_url(self):
        return reverse_lazy("chat-room", kwargs={
            "room_name": ChatRoomModel.objects.filter(Q(name=self.object.name),
                                                      Q(owner=self.object.owner)).first().name})

    # override form_valid, to save owner(creator) of the room
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(CreateChatRoomView, self).form_valid(form)
