from django import forms

from chat.models import ROOM_NAME_MAX_LENGTH


class RoomSortingForm(forms.Form):
    name = forms.CharField(max_length=ROOM_NAME_MAX_LENGTH, help_text="room name", required=False)
    is_private = forms.BooleanField(required=False)
