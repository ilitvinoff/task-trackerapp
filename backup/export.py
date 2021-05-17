import os
import tempfile
import uuid

from django.db.models import Q
from djqscsv import write_csv

from chat.models import (
    ChatRoomModel, ChatMessageModel
)
from tasktracker.settings import MEDIA_ROOT
from trackerapp.models import (
    TaskModel, Attachment, Message,
)

BASE_BACKUP_PATH = os.path.join(MEDIA_ROOT, "backup")


def write_to_file(filepath, queryset):
    with open(filepath, 'a+') as csv_file:
        write_csv(queryset, csv_file)


def export(request):
    current_user = request.user
    models = {
        'chatroom_qs': ChatRoomModel.objects.filter(owner=current_user).values(
            'name', 'is_private', 'member__id', 'backup_id'),
        'chat_message_qs': ChatMessageModel.objects.filter(owner=current_user).values(
            'body', 'room__backup_id', 'creation_date', 'backup_id'),
        'task_qs': TaskModel.objects.filter(Q(owner=current_user) | Q(assignee=current_user)).values(
            'title', 'description', 'status', 'creation_date', 'owner__id', 'assignee__id', 'backup_id'),
        'task_message_qs': Message.objects.filter(Q(task__owner=current_user) | Q(task__assignee=current_user)).values(
            'body', 'owner__id', 'task__backup_id', 'creation_date', 'backup_id'
        ),
        'task_attachment_qs': Attachment.objects.filter(
            Q(task__owner=current_user) | Q(task__assignee=current_user)).values(
            'owner__id', 'task__backup_id', 'file', 'description', 'creation_date', 'backup_id'
        ),
    }

    temp_dir = tempfile.mkdtemp(dir=BASE_BACKUP_PATH)

    for k, v in models.items():
        filepath = os.path.join(temp_dir, k)
        write_to_file(filepath, v)

    return {}
