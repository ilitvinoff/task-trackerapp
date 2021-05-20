import os

import pandas

from chat.models import ChatMessageModel, ChatRoomModel
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

MODEL_NAME_DICT = {
    CHATROOM_QS_NAME: 'chat.chatroommodel',
    CHAT_MESSAGE_QS_NAME: 'chat.chatmessagemodel',
    TASK_QS_NAME: 'trackerapp.taskmodel',
    TASK_MESSAGE_QS_NAME: 'trackerapp.message',
    TASK_ATTACHMENT_QS_NAME: 'trackerapp.attachment'
}

HAS_CREATION_DATE_FIELD_REQUEST = lambda file: pandas.read_csv(file, parse_dates=['creation_date'])
HAS_NO_CREATION_DATE_FIELD_REQUEST = lambda file: pandas.read_csv(file)

REQUEST_TO_READ_CSV = {
    CHATROOM_QS_NAME: HAS_NO_CREATION_DATE_FIELD_REQUEST,
    CHAT_MESSAGE_QS_NAME: HAS_CREATION_DATE_FIELD_REQUEST,
    TASK_QS_NAME: HAS_CREATION_DATE_FIELD_REQUEST,
    TASK_MESSAGE_QS_NAME: HAS_CREATION_DATE_FIELD_REQUEST,
    TASK_ATTACHMENT_QS_NAME: HAS_CREATION_DATE_FIELD_REQUEST
}

M2M_FIELD_DICT = {
    'member': lambda df: df.member.apply(lambda x: [int(v) for v in x[1:-1].split(',') if v != '']),
    'creation_date': lambda df: df
}
