import django_filters
from django import forms
from django_filters.fields import DateTimeRangeField
from django_filters.widgets import SuffixedMultiWidget

from chat import models as chat_models
from trackerapp import models


class DateInput(forms.DateTimeInput):
    input_type = "date"


class DatePickerRangeDateField(DateTimeRangeField):
    widget = DateInput


class DatePickerRangeDateFilter(django_filters.DateTimeFromToRangeFilter):
    field_class = DatePickerRangeDateField


class CustomDateRangeWidget(SuffixedMultiWidget):
    suffixes = ['after', 'before']

    def decompress(self, value):
        if value:
            return [value.start, value.stop]
        return [None, None]

    def __init__(self, attrs=None):
        widgets = (DateInput, DateInput)
        super().__init__(widgets, attrs)


class DateFilter(django_filters.FilterSet):
    creation_date = django_filters.DateTimeFromToRangeFilter(widget=CustomDateRangeWidget)


class MessageDateFilter(DateFilter):
    class Meta:
        model = models.Message
        fields = ['creation_date', ]


class AttachmentDateFilter(DateFilter):
    class Meta:
        model = models.Attachment
        fields = ['creation_date', ]


class TaskFilter(DateFilter):
    status = django_filters.ChoiceFilter(choices=models.LOAN_STATUS)

    class Meta:
        model = models.TaskModel
        fields = ['creation_date', 'status']


class ChatRoomFilter(django_filters.FilterSet):
    class Meta:
        model = chat_models.ChatRoomModel
        fields = ['name', 'is_private', 'owner', 'member']
