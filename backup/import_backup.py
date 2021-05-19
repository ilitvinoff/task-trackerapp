import csv
import logging
import zipfile
from io import TextIOWrapper
from zipfile import ZipFile

from django import forms
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render
from django.urls import reverse_lazy

from backup import utils
from backup.settings import (
    ORDERED_QS_NAME_LIST_TO_UNPACK,
    MODEL_DICT,
    EXTERNAL_DEPENDENCIES_FIELD_NAMES,
    EXTERNAL_DEPENDENCIES_FIELD_VALUES
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
        reader = csv.DictReader(TextIOWrapper(csv_file, 'utf-8'), dialect=get_dialect(csv_file))

        for instance_dict in reader:
            utils.replace_dict_fields(instance_dict, EXTERNAL_DEPENDENCIES_FIELD_NAMES,
                                      EXTERNAL_DEPENDENCIES_FIELD_VALUES)
            instance = MODEL_DICT[qs_name](**instance_dict)
            print(instance_dict)


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
