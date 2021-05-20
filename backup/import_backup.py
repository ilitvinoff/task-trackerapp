import csv
import json
import logging
import zipfile
from zipfile import ZipFile

from django import forms
from django.core.serializers import deserialize
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render
from django.urls import reverse_lazy

from backup.settings import (
    ORDERED_QS_NAME_LIST_TO_UNPACK,
    MODEL_NAME_DICT, MODEL_DICT, REQUEST_TO_READ_CSV, M2M_FIELD_DICT
)
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


def restore(zip_file, qs_name):
    with zip_file.open(qs_name, 'r') as csv_file:
        df = REQUEST_TO_READ_CSV[qs_name](csv_file)

        df_fields = set(df.columns)
        m2m_fields = df_fields.intersection(set(M2M_FIELD_DICT.keys()))

        if m2m_fields:
            for m2m_field in m2m_fields:
                df[m2m_field] = M2M_FIELD_DICT[m2m_field](df)

        if 'creation_date' in df_fields:
            del df['creation_date']

        for record in df.to_dict(orient='records'):
            obj_model_as_dict = {
                'model': MODEL_NAME_DICT[qs_name],
                'fields': record
            }

            obj_model_as_json = f"[{json.dumps(obj_model_as_dict)}]"
            deserialized_data = deserialize("json", obj_model_as_json)

            for deserialized_instance in deserialized_data:
                if MODEL_DICT[qs_name].objects.filter(backup_id=deserialized_instance.object.backup_id).first():
                    continue

                deserialized_instance.save()
                # if deserialized_instance.m2m_data:
                #     for m2m_field in deserialized_instance.m2m_data.keys():
                #         deserialized_instance

            print(obj_model_as_json)


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
                restore(zip_file, qs_name)
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
