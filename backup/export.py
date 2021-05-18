import csv
import os
import shutil
import tempfile
import time
from zipfile import ZipFile

from django.db.models import Q
from django.http import HttpResponse, Http404

from backup.settings import (
    BASE_BACKUP_PATH,
    CHATROOM_QS_NAME,
    CHAT_MESSAGE_QS_NAME,
    TASK_QS_NAME,
    TASK_MESSAGE_QS_NAME,
    TASK_ATTACHMENT_QS_NAME,
    QS_DICT,
    MODEL_DICT
)
from tasktracker.settings import MEDIA_ROOT


def get_all_qs_as_dict(current_user):
    return {
        CHATROOM_QS_NAME: MODEL_DICT[CHATROOM_QS_NAME].objects.filter(owner=current_user).values(
            *QS_DICT[CHATROOM_QS_NAME]),
        CHAT_MESSAGE_QS_NAME: MODEL_DICT[CHAT_MESSAGE_QS_NAME].objects.filter(owner=current_user).values(
            *QS_DICT[CHAT_MESSAGE_QS_NAME]),
        TASK_QS_NAME: MODEL_DICT[TASK_QS_NAME].objects.filter(Q(owner=current_user) | Q(assignee=current_user)).values(
            *QS_DICT[TASK_QS_NAME]),
        TASK_MESSAGE_QS_NAME: MODEL_DICT[TASK_MESSAGE_QS_NAME].objects.filter(
            Q(task__owner=current_user) | Q(task__assignee=current_user)).values(
            *QS_DICT[TASK_MESSAGE_QS_NAME]),
        TASK_ATTACHMENT_QS_NAME: MODEL_DICT[TASK_ATTACHMENT_QS_NAME].objects.filter(
            Q(task__owner=current_user) | Q(task__assignee=current_user)).values(*QS_DICT[TASK_ATTACHMENT_QS_NAME]),
    }


def write_to_file(filepath, queryset, qs_name):
    with open(filepath, 'a+') as csv_file:
        fieldnames = QS_DICT[qs_name]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for model_instance in queryset:
            writer.writerow(model_instance)

def get_attachment_filename_list(attachment_qs):
    result = []

    for attachment in attachment_qs:
       result.append(attachment['file'])

    return result

def compress_attachmnet_files(zipper,attachment_filename_list):
    for attachment in attachment_filename_list:
        zipper.write(filename=os.path.join(MEDIA_ROOT, attachment.file), arcname=attachment.file)


def compress(dirpath, attachment_filename_list):
    files = os.listdir(dirpath)
    zip_name = os.path.join(dirpath, time.strftime("%Y%m%d-%H%M%S") + '.zip')

    with ZipFile(zip_name, 'w') as zipper:
        # we sure that the content of dir is files only,
        # so we do not check if unit is file or not...
        for file in files:
            zipper.write(filename=os.path.join(dirpath, file), arcname=file)

        compress_attachmnet_files(zipper,attachment_filename_list)

    return zip_name


def get_temp_dir():
    if not os.path.exists(BASE_BACKUP_PATH):
        os.mkdir(BASE_BACKUP_PATH)

    return tempfile.mkdtemp(dir=BASE_BACKUP_PATH)


def export(request):
    current_user = request.user

    # get all query sets available for backup process
    all_qs = get_all_qs_as_dict(current_user)
    attachment_filename_list = get_attachment_filename_list(all_qs[TASK_ATTACHMENT_QS_NAME])

    temp_dir = get_temp_dir()

    # each "queryset_obj" is written to its own file
    for qs_name, qs_value in all_qs.items():
        filepath = os.path.join(temp_dir, qs_name)
        write_to_file(filepath=filepath, queryset=qs_value, qs_name=qs_name)

    # compress queryset's files to zip archive
    zip_name = compress(temp_dir,attachment_filename_list)

    # send zip-file to user
    if os.path.exists(zip_name):

        try:
            with open(zip_name, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
                response['Content-Disposition'] = 'inline; filename=' + os.path.basename(zip_name)
                return response

        # remove temp_dir after response is sent
        finally:
            shutil.rmtree(temp_dir)

    raise Http404
