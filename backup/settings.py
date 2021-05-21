import os

import pandas
from django.contrib.auth.models import User
from django.utils.datetime_safe import datetime

from chat.models import ChatMessageModel, ChatRoomModel
from chat.utils import restore_file
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


def has_creation_date(file):
    return pandas.read_csv(file, parse_dates=['creation_date'])


def has_no_creation_date(file):
    return pandas.read_csv(file)


REQUEST_TO_READ_CSV = {
    CHATROOM_QS_NAME: has_no_creation_date,
    CHAT_MESSAGE_QS_NAME: has_creation_date,
    TASK_QS_NAME: has_creation_date,
    TASK_MESSAGE_QS_NAME: has_creation_date,
    TASK_ATTACHMENT_QS_NAME: has_creation_date
}

FIELDS_NEED_TO_CONVERT = {
    # member is many to many field and stored to file like "[1,2,3]" when serializing,
    # so list representing as string. To unpack it correctly let's use func (watch sub)
    'member': lambda pandas_dataframe: pandas_dataframe.member.apply(
        lambda members_as_string: [int(member) for member in members_as_string[1:-1].split(',') if member != '']),

    # for models serialized with - use_natural_foreign_keys=True attr, such fields as owner, assignee, task, room
    # stored to file with it's username for owner or assignee, and another appropriate values for appropriate fields,
    # thanks django let us to do this, but ...
    # Django deserializer can't deserialize that data correct (LOL OMG WTF !!!!), that's why we need
    # dance with a tambourine around the data to deserialize it (LOL OMG WTF !!!!)
    'owner': lambda pandas_dataframe: pandas_dataframe.owner.apply(
        lambda x: User.objects.get(username=x[2:-2]).id if type(x) != int else x),
    'assignee': lambda pandas_dataframe: pandas_dataframe.assignee.apply(
        lambda x: User.objects.get(username=x[2:-2]).id if type(x) != int else x),
    'task': lambda pandas_dataframe: pandas_dataframe.task.apply(lambda x: TaskModel.objects.get(backup_id=x).id),
    'room': lambda pandas_dataframe: pandas_dataframe.room.apply(lambda x: ChatRoomModel.objects.get(backup_id=x).id),

    # replace creation date with datetime.now()
    'creation_date': lambda pandas_dataframe: pandas_dataframe.creation_date.apply(lambda x: datetime.now()),
}

BACKUP_FILE_FUNC = {
    TASK_ATTACHMENT_QS_NAME: restore_file
}
