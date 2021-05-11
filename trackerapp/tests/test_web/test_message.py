from django.test import TestCase
from django.urls import reverse_lazy

from trackerapp.models import Message
from trackerapp.tests import initiators


class MessageListView(TestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def test_valid_user_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Message)
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        # owner of the related to message task
        response = self.client.get(reverse_lazy('comment-list', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 200)

        # assignee of the related to message task
        response = self.client.get(reverse_lazy('comment-list', kwargs={'pk': self.task2.id}))
        self.assertEqual(response.status_code, 200)

    def test_bad_user_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Message)
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.client.get(reverse_lazy('comment-list', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Message)
        response = self.client.get(reverse_lazy('comment-list', kwargs={'pk': self.task1.id}), follow=True)
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/task/{}/message/'.format(self.task1.id), 302))

    def test_pagination(self):
        initiators.create_lists_for_different_users(self, page_count=initiators.PAGE_COUNT, model_class=Message)
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])
        page_count = 1

        while True:
            response = self.client.get(
                reverse_lazy('comment-list', kwargs={'pk': self.task1.id}) + '?page={}'.format(page_count))

            try:
                query_list = set(response.context_data['object_list'])
                self.user1_item_set.difference_update(query_list)
            except Exception:
                page_count -= 1
                break
            page_count += 1

        self.assertEqual(page_count, initiators.PAGE_COUNT)
        self.assertEqual(len(self.user1_item_set), 0)

    def test_filter_by_date(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Message)
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        from_date = initiators.INITIAL_CREATION_DATE[1]
        till_date = initiators.INITIAL_CREATION_DATE[-2]

        response = self.client.post(reverse_lazy('comment-list', kwargs={'pk': self.task1.id}),
                                    data={'from_date': from_date, 'till_date': till_date})
        query_list = set(response.context_data['object_list'])

        self.assertEqual(len(query_list), len(initiators.INITIAL_CREATION_DATE) - 2)

        for message in query_list:
            self.assertTrue(till_date >= message.creation_date >= from_date)


class MessageDetailTestCase(TestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)
        self.message = Message.objects.create(body="test message",
                                              owner=self.user1,
                                              task=self.task1)

    def get_url(self):
        self.pk = Message.objects.get(body__exact="test message", owner__exact=self.user1,
                                      task__exact=self.task1).id
        return reverse_lazy('comment-detail', kwargs={'pk': self.pk})

    def test_unauthorized_user(self):
        response = self.client.get(self.get_url(), follow=True)
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=' + str(reverse_lazy('comment-detail', kwargs={'pk': self.pk})), 302))

    def test_bad_user_try_get_message(self):
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_valid_user_get_message(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['message'].id, self.pk)


class MessageCreateTestCase(TestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def test_owner_and_task_assign_into_message_automatically(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])
        data = {'body': 'test message create'}

        response = self.client.post(reverse_lazy('message-create', kwargs={'pk': self.task1.id}), data=data,
                                    follow=True)
        created_message = Message.objects.get(body='test message create')
        self.assertEqual(response.redirect_chain[0],
                         (reverse_lazy('comment-detail', kwargs={'pk': created_message.id}), 302))
        self.assertEqual(created_message.owner, self.user1)
        self.assertEqual(created_message.task, self.task1)

    def test_unauthorized_user_creation_request(self):
        data = {'body': 'test message create'}

        response = self.client.post(reverse_lazy('message-create', kwargs={'pk': self.task1.id}), data=data,
                                    follow=True)
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/task/{}/message/create/'.format(self.task1.id), 302))


class MessageUpdateDeleteTestCase(TestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)
        self.message = Message.objects.create(body="test message",
                                              owner=self.user1,
                                              task=self.task1)

    def get_response(self, url_name):
        return self.client.post(reverse_lazy(url_name, kwargs={'pk': self.message.id}),
                                data={'body': 'new message body'}, follow=True)

    def test_unauthorized_request(self):
        response = self.get_response('message-update')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/message/{}/update/'.format(self.message.id), 302))

        response = self.get_response('message-delete')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/message/{}/delete/'.format(self.message.id), 302))

    def test_bad_user_request(self):
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.get_response('message-update')
        self.assertEqual(response.status_code, 403)

        response = self.get_response('message-delete')
        self.assertEqual(response.status_code, 403)

    def test_valid_user_request(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        response = self.get_response('message-update')
        self.assertEqual(response.redirect_chain[0],
                         (reverse_lazy('comment-detail', kwargs={'pk': self.message.id}), 302))

        response = self.get_response('message-delete')
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('comment-list', kwargs={'pk': self.task1.id}), 302))
