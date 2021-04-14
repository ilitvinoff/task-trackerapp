import datetime
import os

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy
from freezegun import freeze_time

from tasktracker import settings
from trackerapp.models import TaskModel
from trackerapp.views import ITEMS_ON_PAGE

OWNER_EMAIL = "owner@a.com"
OWNER_CREDENTIALS = ('owner', '12Asasas12')
HACKER_EMAIL = "hacker@b.b"
HACKER_CREDENTIALS = ('hacker', '12test12')
TEST_MEDIA_PATH = os.path.join(settings.BASE_DIR, "test-media")

PAGE_COUNT = 5
# amount of users authorized in tracker app, must be greater or equal 2
USERS_COUNT = 2
INITIAL_CREATION_DATE = sorted([datetime.date.today() - datetime.timedelta(days=i) for i in range(0, ITEMS_ON_PAGE)])
INITIAL_STATUS = ("waiting to start", "in work", "completed")


def taskmodel_test_initial_conditions(self):
    self.owner = get_user_model().objects.create_user(username=OWNER_CREDENTIALS[0],
                                                      password=OWNER_CREDENTIALS[1],
                                                      email=OWNER_EMAIL)
    self.owner.save()

    self.hacker = get_user_model().objects.create_user(username=HACKER_CREDENTIALS[0],
                                                       password=HACKER_CREDENTIALS[1],
                                                       email=HACKER_EMAIL)
    self.hacker.save()


class TaskAssigneeListTestCase(TestCase):
    def setUp(self) -> None:
        taskmodel_test_initial_conditions(self)

    def create_lists_for_different_users(self, page_count):
        self.owner_task_set = set()
        self.hacker_task_list = set()
        self.status_count = {}
        date_index = 0
        status_index = 0

        for i in range(0, ITEMS_ON_PAGE * page_count * USERS_COUNT):

            if date_index >= len(INITIAL_CREATION_DATE):
                date_index = 0
            if status_index >= len(INITIAL_STATUS):
                status_index = 0

            with freeze_time(INITIAL_CREATION_DATE[date_index]):
                if i % USERS_COUNT == 0:
                    task = TaskModel.objects.create(owner=self.owner, assignee=self.hacker, title=i, description=i,
                                                    status=INITIAL_STATUS[status_index])
                    task.save()
                    self.owner_task_set.add(task)
                else:
                    task = TaskModel.objects.create(owner=self.hacker, assignee=self.owner, title=i, description=i,
                                                    status=INITIAL_STATUS[status_index])
                    task.save()
                    self.hacker_task_list.add(task)
                    date_index += 1
                    self.status_count[INITIAL_STATUS[status_index]] = self.status_count.get(
                        INITIAL_STATUS[status_index], 0) + 1
                    status_index += 1

    def test_list_related_to_owner_only(self):
        self.create_lists_for_different_users(page_count=1)

        self.client.login(username=self.owner.username, password=OWNER_CREDENTIALS[1])
        response = self.client.get(reverse_lazy("index"))
        task_queryset_result = set(response.context_data['object_list'])
        self.assertEqual(len(task_queryset_result), ITEMS_ON_PAGE)
        self.assertSetEqual(self.owner_task_set, task_queryset_result)

    def test_pagination(self):
        self.create_lists_for_different_users(page_count=PAGE_COUNT)

        self.client.login(username=self.owner.username, password=OWNER_CREDENTIALS[1])
        page_count = 1

        while True:
            response = self.client.get(reverse_lazy("index") + '?page={}'.format(page_count))

            try:
                query_list = set(response.context_data['object_list'])
                self.owner_task_set.difference_update(query_list)
            except Exception:
                page_count -= 1
                break
            page_count += 1

        self.assertEqual(page_count, PAGE_COUNT)
        self.assertEqual(len(self.owner_task_set), 0)

    def test_filter_options_tasks_by_date(self):
        self.create_lists_for_different_users(page_count=1)
        self.client.login(username=self.owner.username, password=OWNER_CREDENTIALS[1])

        from_date = INITIAL_CREATION_DATE[1]
        till_date = INITIAL_CREATION_DATE[-2]

        response = self.client.post(reverse_lazy("index"), data={'from_date': from_date, 'till_date': till_date})
        query_list = set(response.context_data['object_list'])

        self.assertEqual(len(query_list), len(INITIAL_CREATION_DATE) - 2)

        for task in query_list:
            self.assertTrue(till_date >= task.creation_date >= from_date)

    def test_filter_tasks_by_status(self):
        self.create_lists_for_different_users(page_count=1)
        self.client.login(username=self.owner.username, password=OWNER_CREDENTIALS[1])

        for current_status in range(0, len(INITIAL_STATUS)):
            response = self.client.post(reverse_lazy('index'),
                                        data={'choose_status': INITIAL_STATUS[current_status]})
            query_list = set(response.context_data['object_list'])
            self.assertEqual(len(query_list), self.status_count[INITIAL_STATUS[current_status]])

            for task in query_list:
                self.assertEqual(task.status, INITIAL_STATUS[current_status])

    def test_assignee_list(self):
        self.create_lists_for_different_users(page_count=1)
        self.client.login(username=self.owner.username, password=OWNER_CREDENTIALS[1])

        response = self.client.get(reverse_lazy("assigned-tasks"))
        query_list = set(response.context_data['object_list'])
        self.assertSetEqual(self.hacker_task_list, query_list)


class TaskDetailTestCase(TestCase):
    def setUp(self) -> None:
        taskmodel_test_initial_conditions(self)
        self.owner_task = TaskModel.objects.create(owner=self.owner, title='test title', description='test description')

    def test_unauthorized_user(self):
        pk = TaskModel.objects.get(owner__email__exact=OWNER_EMAIL).id
        task_url = reverse_lazy('task-detail', kwargs={'pk': pk})
        response = self.client.get(task_url, follow=True)
        self.assertEqual(response.redirect_chain[0], ('/accounts/login/?next=/task/{}/'.format(pk), 302))

    def test_bad_user_try_get_task(self):
        self.client.login(username=self.hacker.username, password=HACKER_CREDENTIALS[1])
        pk = TaskModel.objects.get(owner__email__exact=OWNER_EMAIL).id
        task_url = reverse_lazy('task-detail', kwargs={'pk': pk})

        response = self.client.get(task_url)
        self.assertEqual(response.status_code, 403)

    def test_valid_user_get_task(self):
        self.client.login(username=self.owner.username, password=OWNER_CREDENTIALS[1])
        pk = TaskModel.objects.get(owner__email__exact=OWNER_EMAIL).id
        task_url = reverse_lazy('task-detail', kwargs={'pk': pk})

        response = self.client.get(task_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['taskmodel'].id, pk)
