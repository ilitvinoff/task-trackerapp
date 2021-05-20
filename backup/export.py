import csv
import json
import os
import shutil
import tempfile
import time
from zipfile import ZipFile

from django.core.serializers import serialize
from django.db.models import Q
from django.http import HttpResponse, Http404

from backup.settings import (
    BASE_BACKUP_PATH,
    CHATROOM_QS_NAME,
    CHAT_MESSAGE_QS_NAME,
    TASK_QS_NAME,
    TASK_MESSAGE_QS_NAME,
    TASK_ATTACHMENT_QS_NAME,
    MODEL_DICT
)
from tasktracker.settings import MEDIA_ROOT


def json_loads_backup_to_dict(current_user):
    return {
        CHATROOM_QS_NAME: json.loads(
            serialize("json", MODEL_DICT[CHATROOM_QS_NAME].objects.filter(owner=current_user),
                      use_natural_primary_keys=True)),
        CHAT_MESSAGE_QS_NAME: json.loads(
            serialize("json", MODEL_DICT[CHAT_MESSAGE_QS_NAME].objects.filter(owner=current_user),
                      use_natural_foreign_keys=True,
                      use_natural_primary_keys=True)),
        TASK_QS_NAME: json.loads(serialize("json", MODEL_DICT[TASK_QS_NAME].objects.filter(
            Q(owner=current_user) | Q(assignee=current_user)), use_natural_primary_keys=True)),
        TASK_MESSAGE_QS_NAME: json.loads(serialize("json", MODEL_DICT[TASK_MESSAGE_QS_NAME].objects.filter(
            Q(task__owner=current_user) | Q(task__assignee=current_user)), use_natural_foreign_keys=True,
                                                   use_natural_primary_keys=True)),
        TASK_ATTACHMENT_QS_NAME: json.loads(serialize("json", MODEL_DICT[TASK_ATTACHMENT_QS_NAME].objects.filter(
            Q(task__owner=current_user) | Q(task__assignee=current_user)), use_natural_foreign_keys=True,
                                                      use_natural_primary_keys=True))
    }


def write_to_file(filepath, backup_data):
    if len(backup_data) == 0:
        return

    with open(filepath, 'a+') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=backup_data[0]['fields'].keys())
        writer.writeheader()

        for model_instance in backup_data:
            writer.writerow(model_instance['fields'])


def compress_attachment_files(zipper, attachment_data):
    for attachment in attachment_data:
        zipper.write(filename=os.path.join(MEDIA_ROOT, attachment['fields']['file']),
                     arcname=attachment['fields']['file'])


def compress(dirpath, attachment_data):
    files = os.listdir(dirpath)
    zip_name = os.path.join(dirpath, time.strftime("%Y%m%d-%H%M%S") + '.zip')

    with ZipFile(zip_name, 'w') as zipper:
        # we sure that the content of dir is files only,
        # so we do not check if unit is file or not...
        for file in files:
            zipper.write(filename=os.path.join(dirpath, file), arcname=file)

        # compress files separately for convenience when importing
        compress_attachment_files(zipper, attachment_data)

    return zip_name


def get_temp_dir():
    if not os.path.exists(BASE_BACKUP_PATH):
        os.mkdir(BASE_BACKUP_PATH)

    return tempfile.mkdtemp(dir=BASE_BACKUP_PATH)


def export(request):
    current_user = request.user

    # get all query sets available for backup process
    backup_dict = json_loads_backup_to_dict(current_user)

    temp_dir = get_temp_dir()

    # each "queryset_obj" is written to its own file
    for qs_name, data_value in backup_dict.items():
        filepath = os.path.join(temp_dir, qs_name)
        write_to_file(filepath=filepath, backup_data=data_value)

    # compress queryset's files to zip archive
    zip_name = compress(temp_dir, backup_dict[TASK_ATTACHMENT_QS_NAME])

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
