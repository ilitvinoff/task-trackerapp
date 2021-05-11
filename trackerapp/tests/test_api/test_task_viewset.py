from django.urls import reverse_lazy
from rest_framework.test import APITestCase

from trackerapp.api.serializers import TaskSerializer
from trackerapp.models import TaskModel
from trackerapp.tests import initiators


class TaskViewSetListTestCase(APITestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)
        self.task1.delete()
        self.task2.delete()

    def test_valid_user_get_list(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=TaskModel)
        initiators.set_credentials(self, initiators.USER1_CREDENTIALS)
        self.user1_item_set.update(self.user2_item_set)
        initial_list = initiators.get_initial_list(TaskSerializer(), self.user1_item_set)

        # owner of the task
        response = self.client.get(reverse_lazy('task-api-list'))
        self.assertEqual(response.status_code, 200)

        try:
            initiators.list_update_difference(response.data['results'], initial_list)

        except ValueError:
            self.assertFalse(True, "element of response's list not present in initial data list")

        # assigned to the task user
        self.client.logout()
        initiators.set_credentials(self, initiators.USER2_CREDENTIALS)

        response = self.client.get(reverse_lazy('task-api-list'))
        self.assertEqual(response.status_code, 200)

        try:
            initiators.list_update_difference(response.data['results'], initial_list)

        except ValueError:
            self.assertFalse(True, "element of response's list not present in initial data list")

    def test_pagination(self):
        initiators.create_lists_for_different_users(self, page_count=initiators.PAGE_COUNT, model_class=TaskModel)
        self.user1_item_set.update(self.user2_item_set)
        initial_list = initiators.get_initial_list(TaskSerializer(), self.user1_item_set)

        initiators.set_credentials(self, initiators.USER1_CREDENTIALS)
        page_count = 1
        expected_page_count = len(initial_list) / initiators.ITEMS_ON_PAGE

        while True:
            response = self.client.get(reverse_lazy("task-api-list") + '?page={}'.format(page_count))

            try:
                initiators.list_update_difference(response.data['results'], initial_list)

            except ValueError:
                self.assertFalse(True, "element of response's list not present in initial data list")
            except KeyError:
                page_count -= 1
                break
            page_count += 1

        self.assertEqual(page_count, expected_page_count)
        self.assertEqual(len(initial_list), 0)

    def test_unauthorized_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=TaskModel)
        response = self.client.get(reverse_lazy('task-api-list'))
        self.assertEqual(response.status_code, 401)


class TaskViewSetDetailTestCase(APITestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def get_url(self):
        self.pk = TaskModel.objects.get(owner__email__exact=initiators.USER1_CREDENTIALS[2]).id
        return reverse_lazy('task-api-detail', kwargs={'pk': self.pk})

    def test_unauthorized_user(self):
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 401)

    def test_bad_user_try_get_task(self):
        initiators.set_credentials(self, initiators.HACKER_CREDENTIALS)

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_valid_user_get_task(self):
        initiators.set_credentials(self, initiators.USER1_CREDENTIALS)

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.pk, "Initial obj mismatched with response obj")


class TaskViewSetCreateTestCase(APITestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def test_valid_request_to_create(self):
        initiators.set_credentials(self, initiators.USER1_CREDENTIALS)

        data = {'title': 'test title', 'description': 'test_description', 'status': 'waiting to start',
                'assignee': self.user2.id}
        response = self.client.post(reverse_lazy('task-api-list'), data=data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['owner'], self.user1.username)
        self.assertEqual(response.data['assignee_username'], self.user2.username)
        self.assertEqual(response.data['title'], 'test title')
        self.assertEqual(response.data['description'], 'test_description')
        self.assertEqual(response.data['status'], 'waiting to start')

    def test_unauthorized_user_request_to_create(self):
        data = {'title': 'test title', 'description': 'test_description', 'status': 'waiting to start',
                'assignee_username': self.user2.username}
        response = self.client.post(reverse_lazy('task-api-list'), data=data)

        self.assertEqual(response.status_code, 401)


class TaskViewSetUpdateDeleteTestCase(APITestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def get_update_response(self):
        return self.client.put(reverse_lazy('task-api-detail', kwargs={'pk': self.task1.id}),
                               data={'title': 'test title', 'description': 'test_description',
                                     'status': 'waiting to start'})

    def get_delete_response(self):
        return self.client.delete(reverse_lazy('task-api-detail', kwargs={'pk': self.task1.id}),
                                  data={'title': 'test title', 'description': 'test_description',
                                        'status': 'waiting to start'})

    def test_unauthorized_request(self):
        response = self.get_update_response()
        self.assertEqual(response.status_code, 401)

        response = self.get_delete_response()
        self.assertEqual(response.status_code, 401)

    def test_bad_user_request(self):
        initiators.set_credentials(self, initiators.HACKER_CREDENTIALS)

        response = self.get_update_response()
        self.assertEqual(response.status_code, 403)

        response = self.get_delete_response()
        self.assertEqual(response.status_code, 403)

    def test_valid_user_request(self):
        initiators.set_credentials(self, initiators.USER1_CREDENTIALS)

        response = self.get_update_response()
        self.assertEqual(response.status_code, 200)

        response = self.get_delete_response()
        self.assertEqual(response.status_code, 204)

    def test_assignee_try_update_delete(self):
        initiators.set_credentials(self, initiators.USER2_CREDENTIALS)

        response = self.get_update_response()
        self.assertEqual(response.status_code, 403)

        response = self.get_delete_response()
        self.assertEqual(response.status_code, 403)
