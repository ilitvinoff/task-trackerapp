# Create your models here.
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

ROOM_NAME_MAX_LENGTH = 30
MESSAGE_BODY_MAX_LENGTH = 1500


class ChatRoomModel(models.Model):
    name = models.CharField(max_length=ROOM_NAME_MAX_LENGTH, help_text="room name")
    is_private = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner")
    member = models.ManyToManyField(User, related_name="member")

    def __str__(self):
        return f'Room name: "{self.name}", is_private: "{self.is_private}"'

    def get_owner(self):
        return self.owner

    def get_absolute_url(self):
        """
        Returns the url to access a particular instance of the model.
        """
        return reverse("room-detail", args=[str(self.id)])


class ChatMessageModel(models.Model):
    body = models.CharField(max_length=MESSAGE_BODY_MAX_LENGTH, help_text="message")
    owner = models.OneToOneField(User, on_delete=models.DO_NOTHING, null=True)
    room = models.ForeignKey(ChatRoomModel, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return (f'body:\n"{self.body}"\nowner: {self.owner}')
