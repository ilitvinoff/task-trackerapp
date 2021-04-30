# Create your views here.
from django.shortcuts import render

from trackerapp.models import UserProfile


def index(request):
    userprofile_id = UserProfile.objects.get(owner_id=request.user.id).id
    return render(request, 'chat/index.html', context={'userprofile_id': userprofile_id})


def room(request, room_name):
    userprofile_id = UserProfile.objects.get(owner_id=request.user.id).id
    return render(request, 'room.html', {
        'room_name': room_name, 'userprofile_id': userprofile_id
    })
