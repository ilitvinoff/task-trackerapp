import logging
from zipfile import ZipFile
import zipfile

from django import forms
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.urls import reverse_lazy
from django.shortcuts import render

from backup.settings import (
    BASE_BACKUP_PATH,
ORDERED_QS_NAME_LIST_TO_UNPACK,
    QS_DICT,
    MODEL_DICT
)
from tasktracker.exceptions import BadFileContent

class UploadFileForm(forms.Form):
    file = forms.FileField()

def validate_zip_content(zip_file):
    content = zip_file.namelist()

    if len(content)!=len(ORDERED_QS_NAME_LIST_TO_UNPACK):
        raise BadFileContent("Invalid count of files inside")

    for qs_name in ORDERED_QS_NAME_LIST_TO_UNPACK:
        if qs_name not in content:
            raise BadFileContent("File: \"{}\" - not exists".format(qs_name))

def restore(zip_file,qs_name):
    with zip_file.open(qs_name) as csv_file:
        pass


def handle_uploaded_file(file):
    if not zipfile.is_zipfile(file):
        raise zipfile.BadZipFile

    with ZipFile(file) as zip_file:
        try:
            validate_zip_content(zip_file)
        except BadFileContent as e:
            logging.warning(e)
            return HttpResponseBadRequest()

        for qs_name in ORDERED_QS_NAME_LIST_TO_UNPACK:
            try:
                restore(zip_file,qs_name)
            except:
                pass

    return HttpResponseRedirect(reverse_lazy("index"))

def import_backup(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            return handle_uploaded_file(request.FILES['file'])
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})