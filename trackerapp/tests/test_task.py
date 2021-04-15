from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy
from django.utils import timezone
from freezegun import freeze_time

from trackerapp.models import TaskModel
from trackerapp.views import ITEMS_ON_PAGE

OWNER_CREDENTIALS = ('owner', '12Asasas12', "owner@a.com")
HACKER_CREDENTIALS = ('hacker', '12test12', "hacker@b.b")
PAGE_COUNT = 5
# amount of users authorized in tracker app, must be greater or equal 2
USERS_COUNT = 2
INITIAL_CREATION_DATE = sorted([timezone.now() - timezone.timedelta(days=i) for i in range(0, ITEMS_ON_PAGE)])
INITIAL_STATUS = ("waiting to start", "in work", "completed")


def get_user(user_credentials):
    return get_user_model().objects.create_user(username=user_credentials[0],
                                                password=user_credentials[1],
                                                email=user_credentials[2])


def taskmodel_test_initial_conditions(self):
    self.owner = get_user(OWNER_CREDENTIALS)
    self.owner.save()

    self.hacker = get_user(HACKER_CREDENTIALS)
    self.hacker.save()


class TaskListTestCase(TestCase):
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

    def get_url(self):
        self.pk = TaskModel.objects.get(owner__email__exact=OWNER_CREDENTIALS[2]).id
        return reverse_lazy('task-detail', kwargs={'pk': self.pk})

    def test_unauthorized_user(self):
        response = self.client.get(self.get_url(), follow=True)
        self.assertEqual(response.redirect_chain[0], ('/accounts/login/?next=/task/{}/'.format(self.pk), 302))

    def test_bad_user_try_get_task(self):
        self.client.login(username=self.hacker.username, password=HACKER_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_valid_user_get_task(self):
        self.client.login(username=self.owner.username, password=OWNER_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['taskmodel'].id, self.pk)


class TaskCreateTestCase(TestCase):
    def setUp(self) -> None:
        taskmodel_test_initial_conditions(self)

    def test_request_user_assigned_as_task_owner(self):
        self.client.login(username=self.owner.username, password=OWNER_CREDENTIALS[1])
        response = self.client.post(reverse_lazy('create-task'),
                                    data={'title': 'test title', 'description': 'test_description',
                                          'status': 'waiting to start'}, follow=True)
        created_task = TaskModel.objects.filter(title__exact='test title',
                                                description__exact='test_description').first()
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('task-detail', kwargs={'pk': created_task.id}), 302))
        self.assertEqual(created_task.owner.id, self.owner.id)


class TaskUpdateDeleteTestCase(TestCase):
    def setUp(self) -> None:
        taskmodel_test_initial_conditions(self)

    def get_test_task(self):
        return TaskModel.objects.create(owner=self.owner, assignee=self.hacker, title='1', description='2',
                                        status='waiting to start')

    def get_response(self, created_task, url_name):
        return self.client.post(reverse_lazy(url_name, kwargs={'pk': created_task.id}),
                                data={'title': 'test title', 'description': 'test_description',
                                      'status': 'waiting to start'}, follow=True)

    def test_unauthorized_request(self):
        created_task = self.get_test_task()

        response = self.get_response(created_task, 'update-task')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/task/{}/update/'.format(created_task.id), 302))

        response = self.get_response(created_task, 'update-task-status')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/task/{}/status-update/'.format(created_task.id), 302))

        response = self.get_response(created_task, 'delete-task')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/task/{}/delete/'.format(created_task.id), 302))

    def test_bad_user_request(self):
        created_task = self.get_test_task()
        get_user_model().objects.create_user(username='mytko',
                                             password=OWNER_CREDENTIALS[1],
                                             email='mytko@brytko.com')
        self.client.login(username='mytko', password=OWNER_CREDENTIALS[1])

        response = self.get_response(created_task, 'update-task')
        self.assertEqual(response.status_code, 403)

        response = self.get_response(created_task, "update-task-status")
        self.assertEqual(response.status_code, 403)

        response = self.get_response(created_task, 'delete-task')
        self.assertEqual(response.status_code, 403)

    def test_valid_user_request(self):
        created_task = self.get_test_task()
        self.client.login(username=self.owner.username, password=OWNER_CREDENTIALS[1])

        response = self.get_response(created_task, 'update-task')
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('task-detail', kwargs={'pk': created_task.id}), 302))

        response = self.get_response(created_task, "update-task-status")
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('task-detail', kwargs={'pk': created_task.id}), 302))

        response = self.get_response(created_task, 'delete-task')
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('index'), 302))
