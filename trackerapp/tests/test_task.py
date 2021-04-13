import os

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy

from tasktracker import settings
from trackerapp.models import TaskModel

OWNER_EMAIL = "owner@a.com"
OWNER_CREDENTIALS = ('owner', '12Asasas12')
HACKER_EMAIL = "hacker@b.b"
HACKER_CREDENTIALS = ('hacker', '12test12')
TEST_MEDIA_PATH = os.path.join(settings.BASE_DIR, "test-media")
ITEMS_ON_PAGE = 5
PAGE_COUNT = 5


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

        for i in range(0, ITEMS_ON_PAGE * page_count * 2):
            if i % 2 == 0:
                task = TaskModel.objects.create(owner=self.owner, assignee=self.hacker, title=i, description=i)
                task.save()
                self.owner_task_set.add(task)
            else:
                task = TaskModel.objects.create(owner=self.hacker, assignee=self.owner, title=i, description=i)
                task.save()
                self.hacker_task_list.add(task)

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
