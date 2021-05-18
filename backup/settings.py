import os

from chat.models import ChatRoomModel, ChatMessageModel
from tasktracker.settings import MEDIA_ROOT
from trackerapp.models import TaskModel, Message, Attachment

BASE_BACKUP_PATH = os.path.join(MEDIA_ROOT, "backup")
CHATROOM_QS_NAME = 'chatroom_qs'
CHAT_MESSAGE_QS_NAME = 'chat_message_qs'
TASK_QS_NAME = 'task_qs'
TASK_MESSAGE_QS_NAME = 'task_message_qs'
TASK_ATTACHMENT_QS_NAME = 'task_attachment_qs'

QS_DICT = {
    CHATROOM_QS_NAME: ('name', 'is_private', 'member__id', 'backup_id'),
    CHAT_MESSAGE_QS_NAME: ('body', 'room__backup_id', 'creation_date', 'backup_id'),
    TASK_QS_NAME: ('title', 'description', 'status', 'creation_date', 'owner__id', 'assignee__id', 'backup_id'),
    TASK_MESSAGE_QS_NAME: ('body', 'owner__id', 'task__backup_id', 'creation_date', 'backup_id'),
    TASK_ATTACHMENT_QS_NAME: ('owner__id', 'task__backup_id', 'file', 'description', 'creation_date', 'backup_id')
}

MODEL_DICT = {
    CHATROOM_QS_NAME: ChatRoomModel,
    CHAT_MESSAGE_QS_NAME: ChatMessageModel,
    TASK_QS_NAME: TaskModel,
    TASK_MESSAGE_QS_NAME: Message,
    TASK_ATTACHMENT_QS_NAME: Attachment
}
