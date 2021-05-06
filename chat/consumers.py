import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import PermissionDenied

from chat.models import ChatRoomModel, ChatMessageModel


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.room_group_pk = 'chat_pk_%s' % self.scope['url_route']['kwargs']['pk']
        except KeyError as e:
            raise KeyError(e)

            # Join room group
        await self.channel_layer.group_add(
            self.room_group_pk,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_pk,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)

        try:
            message = text_data_json['message']
            pk = text_data_json['pk']
            message_owner = self.scope['user']
        except KeyError as e:
            raise KeyError(e)

        try:
            room = await sync_to_async(ChatRoomModel.objects.get)(pk=pk)
            room_members = await sync_to_async(room.member.all)()
            room_owner = await sync_to_async(room.get_owner)()

        except ChatRoomModel.DoesNotExist as e:
            raise ChatRoomModel.DoesNotExist(e)

        if not (message_owner == room_owner or message_owner not in room_members):
            raise PermissionDenied(f"User: \"{message_owner}\" has no permission to write in room: \"{room.name}\"")

        await sync_to_async(ChatMessageModel(body=message, owner=message_owner, room=room).save)()

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_pk,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
