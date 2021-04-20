from django.urls import reverse_lazy
from rest_framework.test import APITestCase

from trackerapp.models import Message
from trackerapp.serializers import MessageSerializer
from trackerapp.tests import initiators


class MessageListView(APITestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def test_valid_user_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Message)
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        # owner of the related to message task
        response = self.client.get(reverse_lazy('task-message-list-api', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 200)

        # assignee of the related to message task
        response = self.client.get(reverse_lazy('task-message-list-api', kwargs={'pk': self.task2.id}))
        self.assertEqual(response.status_code, 200)

    def test_bad_user_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Message)
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.client.get(reverse_lazy('task-message-list-api', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Message)
        response = self.client.get(reverse_lazy('task-message-list-api', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 403)

    def test_pagination(self):
        initiators.create_lists_for_different_users(self, page_count=initiators.PAGE_COUNT, model_class=Message)
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])
        page_count = 1
        initial_list = [MessageSerializer().to_representation(item) for item in self.user1_item_set]

        while True:
            response = self.client.get(
                reverse_lazy('task-message-list-api', kwargs={'pk': self.task1.id}) + '?page={}'.format(page_count))

            try:
                query_list = response.data['results']

                for item in query_list:
                    for i in range(0, len(initial_list)):

                        if initial_list[i]['id'] == item['id'] and initial_list[i]['body'] == item['body']:
                            del initial_list[i]
                            break

            except ValueError:
                self.assertFalse(True, "element of response's list not present in initial data list")
            except KeyError:
                page_count -= 1
                break
            page_count += 1

        self.assertEqual(page_count, initiators.PAGE_COUNT)
        self.assertEqual(len(initial_list), 0)


class MessageDetailTestCase(APITestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)
        self.message = Message.objects.create(body="test message",
                                              owner=self.user1,
                                              task=self.task1)

    def get_url(self):
        self.pk = Message.objects.get(body__exact="test message", owner__exact=self.user1,
                                      task__exact=self.task1).id
        return reverse_lazy('message-api-detail', kwargs={'pk': self.pk})

    def test_unauthorized_user(self):
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_bad_user_try_get_message(self):
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_valid_user_get_message(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.pk, "Initial obj mismatched with response obj")


class MessageCreateTestCase(APITestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def test_owner_and_task_assign_into_message_automatically(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])
        data = {'body': 'test message create', 'task_id': self.task1.id}

        response = self.client.post(reverse_lazy('message-api-list'), data=data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['owner'], self.user1.username)
        self.assertEqual(response.data['task_assigned_to'], self.task1.assignee.username)

    def test_unauthorized_user_creation_request(self):
        data = {'body': 'test message create', 'pk': self.task1.id}

        response = self.client.post(reverse_lazy('message-api-list'), data=data)
        self.assertEqual(response.status_code, 403)


class MessageUpdateDeleteTestCase(APITestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)
        self.message = Message.objects.create(body="test message",
                                              owner=self.user1,
                                              task=self.task1)

    def get_update_response(self, url_name):
        return self.client.put(reverse_lazy(url_name, kwargs={'pk': self.message.id}),
                               data={'body': 'new message body'}, )

    def get_delete_response(self, url_name):
        return self.client.delete(reverse_lazy(url_name, kwargs={'pk': self.message.id}),
                                  data={'body': 'new message body'}, )

    def test_unauthorized_request(self):
        response = self.get_update_response('message-api-detail')
        self.assertEqual(response.status_code, 403)

        response = self.get_delete_response('message-api-detail')
        self.assertEqual(response.status_code, 403)

    def test_bad_user_request(self):
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.get_update_response('message-api-detail')
        self.assertEqual(response.status_code, 403)

        response = self.get_delete_response('message-api-detail')
        self.assertEqual(response.status_code, 403)

    def test_valid_user_request(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        response = self.get_update_response('message-api-detail')
        self.assertEqual(response.status_code, 200)

        response = self.get_delete_response('message-api-detail')
        self.assertEqual(response.status_code, 204)
