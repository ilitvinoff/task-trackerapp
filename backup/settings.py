import os

from chat.models import ChatRoomModel, ChatMessageModel
from tasktracker.settings import MEDIA_ROOT
from trackerapp.models import TaskModel, Message, Attachment

"""
Directory path for managing user's data to import/export backup of this data
"""
BASE_BACKUP_PATH = os.path.join(MEDIA_ROOT, "backup")

"""
Names for query sets for each model available for backup
"""
CHATROOM_QS_NAME = 'chatroom_qs'
CHAT_MESSAGE_QS_NAME = 'chat_message_qs'
TASK_QS_NAME = 'task_qs'
TASK_MESSAGE_QS_NAME = 'task_message_qs'
TASK_ATTACHMENT_QS_NAME = 'task_attachment_qs'

ORDERED_QS_NAME_LIST_TO_UNPACK = (
    CHATROOM_QS_NAME,
    CHAT_MESSAGE_QS_NAME,
    TASK_QS_NAME,
    TASK_MESSAGE_QS_NAME,
    TASK_ATTACHMENT_QS_NAME
)
"""
Dictionary that links queryset name and model's fields, that will be returned as result of qs
Used to creat query set, for example :
qs = MODEL_DICT[CHATROOM_QS_NAME].objects.all().values(*QS_DICT[CHATROOM_QS_NAME])
"""
QS_DICT = {
    CHATROOM_QS_NAME: ('name', 'is_private', 'member__id', 'backup_id'),
    CHAT_MESSAGE_QS_NAME: ('body', 'room__backup_id', 'creation_date', 'backup_id'),
    TASK_QS_NAME: ('title', 'description', 'status', 'creation_date', 'owner__id', 'assignee__id', 'backup_id'),
    TASK_MESSAGE_QS_NAME: ('body', 'owner__id', 'task__backup_id', 'creation_date', 'backup_id'),
    TASK_ATTACHMENT_QS_NAME: ('owner__id', 'task__backup_id', 'file', 'description', 'creation_date', 'backup_id')
}

"""
Dictionary that links queryset name and model's class.
Used to creat query set, for example :
qs = MODEL_DICT[CHATROOM_QS_NAME].objects.all()
"""
MODEL_DICT = {
    CHATROOM_QS_NAME: ChatRoomModel,
    CHAT_MESSAGE_QS_NAME: ChatMessageModel,
    TASK_QS_NAME: TaskModel,
    TASK_MESSAGE_QS_NAME: Message,
    TASK_ATTACHMENT_QS_NAME: Attachment
}
