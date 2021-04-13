import datetime

from django.test import TestCase

from trackerapp.forms import (
    TaskSortingForm,
    DateSortingForm,
)


class DateSortingFormTest(TestCase):
    def test_from_date_in_future(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        form_data = {'from_date': tomorrow}
        form = DateSortingForm(data=form_data)
        self.assertFalse(form.is_valid(), "Passing future date in from date field")

    def test_till_date_before_from_date(self):
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        form_data = {'from_date': tomorrow, 'till_date': datetime.date.today()}
        form = DateSortingForm(data=form_data)
        self.assertFalse(form.is_valid(), "Passing when 'till date' before 'from date'")


class TaskSortingFormTest(TestCase):
    def test_status_choices(self):
        form = TaskSortingForm
        expected_choices = {
            ("", "-----"),
            ("waiting to start", "waiting to start"),
            ("in work", "in work"),
            ("completed", "completed"),
        }
        status_choices = set(form.STATUS_CHOICE_LIST)
        self.assertEqual(expected_choices, status_choices)

