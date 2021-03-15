from django import forms
from django.forms.fields import ChoiceField, DateField
from django.forms.widgets import DateInput
from .models import TaskModel


class TaskSortingForm(forms.Form):
    from_date = DateField(label='date from:', widget=DateInput,
                          help_text='Enter the "date from" for lookup...', required=False)
    till_date = DateField(label='date till', widget=DateInput,
                          help_text='Enter the "date until" for lookup ...', required=False)
    STATUS_CHOICE_LIST = list(TaskModel.LOAN_STATUS)
    STATUS_CHOICE_LIST.append(('', '-----'))
    choose_status = ChoiceField(
        label='choose status', choices=STATUS_CHOICE_LIST, required=False)
