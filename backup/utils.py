from django.contrib.auth.models import User

from chat.models import ChatRoomModel
from trackerapp.models import TaskModel

def get_members():
    pass

def get_user_by_id(id):
    return User.objects.get(id=id)


def get_room_by_id(id):
    return ChatRoomModel.objects.get(id=id)


def get_task_by_backup_id(id):
    return TaskModel.objects.get(id=id)


def replace_dict_fields(replace_in_dict, keys_replace_from_dict, values_replace_from_dict):
    """
    This func created to replace (key,pair) value in imported data dictionary
    to appropriate values.

    Example:
    CHATROOM_QS_NAME: ('name', 'is_private', 'member__id', 'backup_id')
    to restore chatroom in correct way, we need replace member__id with User.objects.get(id=member__id)

    :param replace_in_dict:
    dictionary replace in
    :param keys_replace_from_dict: = {old_key_name : new_key_name}
    :param values_replace_from_dict: = {old_key_name : func(id)}
    where func must take id and return appropriate instance
    :return:
    """
    for k in keys_replace_from_dict.keys():
        if k in replace_in_dict:
            replace_in_dict[keys_replace_from_dict[k]] = values_replace_from_dict[k](replace_in_dict[k])
            del replace_in_dict[k]
