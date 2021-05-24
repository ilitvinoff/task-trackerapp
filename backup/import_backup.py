import json
import logging
import zipfile
from collections import defaultdict

import pandas
from django import forms
from django.core.serializers import deserialize
from django.core.serializers.json import DjangoJSONEncoder, DeserializationError
from django.http import HttpResponseBadRequest
from django.shortcuts import render

from backup import utils
from backup.settings import (
    ORDERED_QS_NAME_LIST_TO_UNPACK,
    MODEL_NAME_DICT, MODEL_DICT, REQUEST_TO_READ_CSV, FIELDS_NEED_TO_CONVERT, BACKUP_FILE_TO_STORAGE_FUNC,
)
from tasktracker.exceptions import BadFileContent, FileMissed

DIALECT_CLUSTER_SIZE = 1024


class UploadFileForm(forms.Form):
    file = forms.FileField()


def validate_zip_content(zip_file):
    content = zip_file.namelist()

    for qs_name in ORDERED_QS_NAME_LIST_TO_UNPACK:
        if qs_name not in content:
            raise FileMissed("File: \"{}\" - not exists".format(qs_name))


def add_log_and_report_to_user(qs_name, report_dict, request_user, err_msg=None, creation_msg=None):
    if creation_msg:
        report_dict['restored_models'][MODEL_NAME_DICT[qs_name]].append(creation_msg)
    if err_msg:
        report_dict['errors'].append(err_msg)
        logging.warning(err_msg + f"Request user: {request_user}")


def restore(zip_file, qs_name, request_user, report_dict):
    with zip_file.open(qs_name, 'r') as csv_file:
        try:
            df = REQUEST_TO_READ_CSV[qs_name](csv_file)
        except pandas.errors.ParserError:
            add_log_and_report_to_user(qs_name, report_dict, request_user,
                                       err_msg=f"Can't parse content of the file: {qs_name}.", )
        except pandas.errors.EmptyDataError:
            add_log_and_report_to_user(qs_name, report_dict, request_user,
                                       err_msg=f"Can't parse content of the file: {qs_name}. File is empty/has no header...", )

        df_fields = set(df.columns)

        # Check if we have fields to convert or edit on current model
        fields_to_convert = df_fields.intersection(set(FIELDS_NEED_TO_CONVERT.keys()))

        try:
            if fields_to_convert:
                for field_to_convert in fields_to_convert:
                    df[field_to_convert] = FIELDS_NEED_TO_CONVERT[field_to_convert](df)
        except BadFileContent as e:
            add_log_and_report_to_user(qs_name, report_dict, request_user, err_msg=f"For file '{qs_name}': '{str(e)}'.")

        for record in df.to_dict(orient='records'):
            obj_model_as_dict = {
                'model': MODEL_NAME_DICT[qs_name],
                'fields': record
            }

            obj_model_as_json = f"[{json.dumps(obj_model_as_dict, cls=DjangoJSONEncoder)}]"
            try:
                deserialized_data = deserialize("json", obj_model_as_json)
            except DeserializationError:
                add_log_and_report_to_user(qs_name, report_dict, request_user,
                                           err_msg=f"For file '{qs_name}'. Bad json model format: '{obj_model_as_json}'.")

            for deserialized_instance in deserialized_data:
                if MODEL_DICT[qs_name].objects.filter(
                        backup_id=deserialized_instance.object.backup_id).first():
                    add_log_and_report_to_user(qs_name, report_dict, request_user,
                                               err_msg=f"Instance {str(deserialized_instance.object)} already exists.")
                    continue

                if not utils.is_owner(request_user, deserialized_instance.object):
                    add_log_and_report_to_user(qs_name, report_dict, request_user,
                                               err_msg=f"User is not instance's owner {str(deserialized_instance)}.")
                    continue

                if qs_name in BACKUP_FILE_TO_STORAGE_FUNC.keys():
                    try:
                        BACKUP_FILE_TO_STORAGE_FUNC[qs_name](zip_file, deserialized_instance.object.file)
                    except Exception as e:
                        logging.warning(
                            f"Can't restore file {deserialized_instance.object.file} for {qs_name}. Request user: {request_user}" + str(
                                e))
                        continue

                deserialized_instance.save()
                add_log_and_report_to_user(qs_name, report_dict, request_user,
                                           creation_msg=f"Instance of {type(deserialized_instance.object)} with backup_id : {deserialized_instance.object.backup_id} - created")


def handle_request(request):
    file = request.FILES['file']

    if not zipfile.is_zipfile(file):
        logging.warning(f"User: \"{request.user}\" sent not zip file")
        return HttpResponseBadRequest("File gavno - ne zip")

    with zipfile.ZipFile(file) as zip_file:
        try:
            validate_zip_content(zip_file)
        except FileMissed as e:
            logging.warning(e)
            return HttpResponseBadRequest("Not enough files for backup")

        report_dict = {
            'errors': [],
            'restored_models': defaultdict(list)
        }

        for qs_name in ORDERED_QS_NAME_LIST_TO_UNPACK:
            try:
                restore(zip_file, qs_name, request.user, report_dict)
            except Exception as e:
                logging.warning(f"User: \"{request.user}\". Err: {e}")
                return HttpResponseBadRequest(e)

    return render(request, "import_report.html",
                  {'errors': report_dict['errors'], 'restored_models': dict(report_dict['restored_models'])})


def import_backup(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            return handle_request(request)
    else:
        form = UploadFileForm()
    return render(request, 'upload.html', {'form': form})
