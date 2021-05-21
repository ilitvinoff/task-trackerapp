# Create your models here.
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

ROOM_NAME_MAX_LENGTH = 30
MESSAGE_BODY_MAX_LENGTH = 1500


class ChatRoomModelManager(models.Manager):
    def get_by_natural_key(self, back_up_id):
        return self.get(back_up_id=back_up_id)


class ChatRoomModel(models.Model):
    name = models.CharField(max_length=ROOM_NAME_MAX_LENGTH, help_text="room name", unique=True)
    is_private = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner")
    member = models.ManyToManyField(User, related_name="member", blank=True)
    backup_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    objects = ChatRoomModelManager

    class Meta:
        ordering = ["-is_private", "name"]

    def __str__(self):
        return f'Room name: "{self.name}", is_private: "{self.is_private}"'

    def natural_key(self):
        return (self.backup_id)

    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_owner(self):
        return self.owner

    def get_members(self):
        return self.member.all()

    def get_absolute_url(self):
        """
        Returns the url to access a particular instance of the model.
        """
        return reverse("chat-room", kwargs={"pk": self.id})


class MessageModelManager(models.Manager):
    def get_by_natural_key(self, back_up_id):
        return self.get(back_up_id=back_up_id)


class ChatMessageModel(models.Model):
    body = models.CharField(max_length=MESSAGE_BODY_MAX_LENGTH, help_text="message")
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    room = models.ForeignKey(ChatRoomModel, on_delete=models.CASCADE, null=True)
    creation_date = models.DateTimeField(auto_created=True, auto_now_add=True, null=True)
    backup_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    objects = MessageModelManager

    def __str__(self):
        return (f'body:\n"{self.body}"\nowner: {self.owner}')

    def get_room_owner(self):
        return self.room.owner

    def get_room_members(self):
        return self.room.get_members()

    def get_owner(self):
        return self.owner
