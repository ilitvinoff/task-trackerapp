from django import forms
from django.core.exceptions import ValidationError
from django.forms.fields import ChoiceField, DateField
from django.forms.widgets import DateInput
from .models import TaskModel


class DateInput(forms.DateInput):
    input_type = 'date'


class TaskSortingForm(forms.Form):
    """
    Form for filter by date(from-till) and by status
    """

    from_date = DateField(
        label="date from:",
        widget=DateInput,
        help_text='Format like 03.17.1979',
        required=False,
    )
    till_date = DateField(
        label="date to:",
        widget=DateInput,
        help_text='Format like 03.17.1979',
        required=False,
    )

    STATUS_CHOICE_LIST = list(TaskModel.LOAN_STATUS)
    STATUS_CHOICE_LIST.append(("", "-----"))

    choose_status = ChoiceField(
        label="choose status", choices=STATUS_CHOICE_LIST, required=False
    )

    def clean(self):
        data = super().clean()
        from_date = data.get('from_date')
        till_date = data.get('till_date')

        if from_date and till_date:
            if from_date > till_date:
                raise ValidationError('"date from" must be before "till date"')
        return data
