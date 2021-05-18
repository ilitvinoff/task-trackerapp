import csv
import os
import tempfile
import time
from zipfile import ZipFile

from django.db.models import Q
from django.http import HttpResponse, Http404

from chat.models import (
    ChatRoomModel, ChatMessageModel
)
from tasktracker.settings import MEDIA_ROOT
from trackerapp.models import (
    TaskModel, Attachment, Message,
)

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


def get_all_qs(current_user):
    return {
        CHATROOM_QS_NAME: ChatRoomModel.objects.filter(owner=current_user).values(*QS_DICT[CHATROOM_QS_NAME]),
        CHAT_MESSAGE_QS_NAME: ChatMessageModel.objects.filter(owner=current_user).values(
            *QS_DICT[CHAT_MESSAGE_QS_NAME]),
        TASK_QS_NAME: TaskModel.objects.filter(Q(owner=current_user) | Q(assignee=current_user)).values(
            *QS_DICT[TASK_QS_NAME]),
        TASK_MESSAGE_QS_NAME: Message.objects.filter(
            Q(task__owner=current_user) | Q(task__assignee=current_user)).values(
            *QS_DICT[TASK_MESSAGE_QS_NAME]),
        TASK_ATTACHMENT_QS_NAME: Attachment.objects.filter(
            Q(task__owner=current_user) | Q(task__assignee=current_user)).values(*QS_DICT[TASK_ATTACHMENT_QS_NAME]),
    }


def write_to_file(filepath, queryset, qs_name):
    with open(filepath, 'a+') as csv_file:
        fieldnames = QS_DICT[qs_name]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for model_instance in queryset:
            writer.writerow(model_instance)


def compress_all_from_dir(dirpath):
    files = os.listdir(dirpath)
    zip_name = os.path.join(dirpath, time.strftime("%Y%m%d-%H%M%S") + '.zip')

    with ZipFile(zip_name, 'w') as zipper:
        # we sure that the content of dir is files only,
        # so we do not check if unit is file or not...
        for file in files:
            zipper.write(filename=os.path.join(dirpath, file), arcname=file)

    return zip_name


def export(request):
    current_user = request.user

    all_qs = get_all_qs(current_user)

    temp_dir = tempfile.mkdtemp(dir=BASE_BACKUP_PATH)

    for qs_name, qs_value in all_qs.items():
        filepath = os.path.join(temp_dir, qs_name)
        write_to_file(filepath=filepath, queryset=qs_value, qs_name=qs_name)

    zip_name = compress_all_from_dir(temp_dir)

    if os.path.exists(zip_name):
        try:
            with open(zip_name, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(zip_name)
                return response
        finally:
            pass
    raise Http404
