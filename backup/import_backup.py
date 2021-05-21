import csv
import json
import logging
import zipfile
from zipfile import ZipFile

from django import forms
from django.core.serializers import deserialize
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render
from django.urls import reverse_lazy

from backup.settings import (
    ORDERED_QS_NAME_LIST_TO_UNPACK,
    MODEL_NAME_DICT, MODEL_DICT, REQUEST_TO_READ_CSV, FIELDS_NEED_TO_CONVERT, BACKUP_FILE_FUNC,
)
from chat.utils import is_owner
from tasktracker.exceptions import BadFileContent

DIALECT_CLUSTER_SIZE = 1024


class UploadFileForm(forms.Form):
    file = forms.FileField()


def validate_zip_content(zip_file):
    content = zip_file.namelist()

    for qs_name in ORDERED_QS_NAME_LIST_TO_UNPACK:
        if qs_name not in content:
            raise BadFileContent("File: \"{}\" - not exists".format(qs_name))


def get_dialect(csv_file):
    dialect = csv.Sniffer().sniff(str(csv_file.read(DIALECT_CLUSTER_SIZE)))
    csv_file.seek(0)

    return dialect


def restore(zip_file, qs_name, request_user):
    with zip_file.open(qs_name, 'r') as csv_file:
        df = REQUEST_TO_READ_CSV[qs_name](csv_file)

        df_fields = set(df.columns)

        # Check if we have fields to convert or edit on current model
        fields_to_convert = df_fields.intersection(set(FIELDS_NEED_TO_CONVERT.keys()))

        if fields_to_convert:
            for m2m_field in fields_to_convert:
                df[m2m_field] = FIELDS_NEED_TO_CONVERT[m2m_field](df)

        for record in df.to_dict(orient='records'):
            obj_model_as_dict = {
                'model': MODEL_NAME_DICT[qs_name],
                'fields': record
            }

            obj_model_as_json = f"[{json.dumps(obj_model_as_dict, cls=DjangoJSONEncoder)}]"
            deserialized_data = deserialize("json", obj_model_as_json)

            for deserialized_instance in deserialized_data:
                if not is_owner(request_user, deserialized_instance.object) or MODEL_DICT[qs_name].objects.filter(
                        backup_id=deserialized_instance.object.backup_id).first():
                    continue

                if qs_name in BACKUP_FILE_FUNC.keys():
                    BACKUP_FILE_FUNC[qs_name](zip_file, deserialized_instance.object.file)

                deserialized_instance.save()


def handle_request(request):
    file = request.FILES['file']

    if not zipfile.is_zipfile(file):
        logging.warning(f"User: \"{request.user}\" sent not zip file")
        return HttpResponseBadRequest("File gavno - ne zip")

    with ZipFile(file) as zip_file:
        try:
            validate_zip_content(zip_file)
        except BadFileContent as e:
            logging.warning(e)
            return HttpResponseBadRequest("Not enough files for backup")

        for qs_name in ORDERED_QS_NAME_LIST_TO_UNPACK:
            try:
                restore(zip_file, qs_name, request.user)
            except csv.Error as e:
                logging.warning(f"User: \"{request.user}\" sent bad csv file. Err: {e}")
                return HttpResponseBadRequest()

    return HttpResponseRedirect(reverse_lazy("index"))


def import_backup(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            return handle_request(request)
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})

# TODO Add try exception and logging. Provide a report about backup success.
