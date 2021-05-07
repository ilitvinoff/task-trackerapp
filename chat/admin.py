# Register your models here.
from django.contrib import admin

from .models import ChatRoomModel, ChatMessageModel

admin.site.register(
    ChatRoomModel,
    list_display=["id", "name", "is_private"],
    list_display_links=["id", "name"],
)

admin.site.register(
    ChatMessageModel,
    list_display=["id", "owner", "room"],
    list_display_links=["id"],
    list_filter=("owner", "room"),
)
