import os

from chat.models import ChatMessageModel
from tasktracker.settings import MEDIA_ROOT
from trackerapp.models import TaskModel, Message, Attachment
from . import utils

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

"""
How to restore instances from a backup on import.
From highest to lowest ...
The order is important because for example
restore the message before the task to which the message belongs,
then we will have problems
"""
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
    CHATROOM_QS_NAME: ('name', 'is_private', 'member', 'backup_id'),
    CHAT_MESSAGE_QS_NAME: ('body', 'room__backup_id', 'creation_date', 'backup_id'),
    TASK_QS_NAME: ('title', 'description', 'status', 'creation_date', 'owner__id', 'assignee__id', 'backup_id'),
    TASK_MESSAGE_QS_NAME: ('body', 'owner__id', 'task__backup_id', 'creation_date', 'backup_id'),
    TASK_ATTACHMENT_QS_NAME: ('owner__id', 'task__backup_id', 'file', 'description', 'creation_date', 'backup_id')
}

EXTERNAL_DEPENDENCIES_FIELD_VALUES = {
    'member__id': utils.get_user_by_id,
    'room__backup_id': utils.get_room_by_id,
    'owner__id': utils.get_user_by_id,
    'assignee__id': utils.get_user_by_id,
    'task__backup_id': utils.get_task_by_backup_id
}

EXTERNAL_DEPENDENCIES_FIELD_NAMES = {
    'member__id': "member",
    'room__backup_id': 'room',
    'owner__id': 'owner',
    'assignee__id': 'assignee',
    'task__backup_id': 'task'
}

"""
Dictionary that links queryset name and model's class.
Used to creat query set, for example :
qs = MODEL_DICT[CHATROOM_QS_NAME].objects.all()
"""
MODEL_DICT = {
    CHATROOM_QS_NAME: utils.ChatRoomModel,
    CHAT_MESSAGE_QS_NAME: ChatMessageModel,
    TASK_QS_NAME: TaskModel,
    TASK_MESSAGE_QS_NAME: Message,
    TASK_ATTACHMENT_QS_NAME: Attachment
}
