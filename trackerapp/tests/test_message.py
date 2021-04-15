from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy
from django.utils import timezone
from freezegun import freeze_time

from trackerapp.models import TaskModel, Message
from trackerapp.views import ITEMS_ON_PAGE

USER1_CREDENTIALS = ('user1', '12Asasas12', "shwonder@a.com")
USER2_CREDENTIALS = ('user2', '12Asasas12', "sharikoff@a.com")
HACKER_CREDENTIALS = ('hacker', '12test12', "hacker@b.b")

PAGE_COUNT = 5
INITIAL_CREATION_DATE = sorted([timezone.now() - timezone.timedelta(days=i) for i in range(0, ITEMS_ON_PAGE)])
DEFAULT_STATUS = "waiting to start"


def get_user(user_credentials):
    return get_user_model().objects.create_user(username=user_credentials[0],
                                                password=user_credentials[1],
                                                email=user_credentials[2])


def message_test_initial_conditions(self):
    self.user1 = get_user(USER1_CREDENTIALS)
    self.user1.save()

    self.user2 = get_user(USER2_CREDENTIALS)
    self.user2.save()

    self.hacker = get_user(HACKER_CREDENTIALS)
    self.hacker.save()

    self.task1 = TaskModel.objects.create(owner=self.user1, assignee=self.user2, title='task1',
                                          description='test description', status=DEFAULT_STATUS)
    self.task1.save()
    self.task2 = TaskModel.objects.create(owner=self.user2, assignee=self.user1, title='task2',
                                          description='test description', status=DEFAULT_STATUS)
    self.task2.save()


class MessageListView(TestCase):
    def create_lists_for_different_users(self, page_count):
        self.user1_message_set = set()
        self.user2_message_set = set()
        self.message_for_owner_count = {}
        message_owners = [self.user1, self.user2]
        users_count = len(message_owners)
        owner_index = 1
        date_index = 0

        for i in range(0, ITEMS_ON_PAGE * page_count * users_count):

            if date_index >= len(INITIAL_CREATION_DATE):
                date_index = 0

            if owner_index >= len(message_owners):
                owner_index = 0

            with freeze_time(INITIAL_CREATION_DATE[date_index]):

                if i % users_count == 0:
                    message = Message.objects.create(task=self.task1, body=i, owner=message_owners[owner_index])
                    message.save()
                    self.user1_message_set.add(message)

                else:
                    message = Message.objects.create(task=self.task2, body=i, owner=message_owners[owner_index])
                    message.save()
                    self.user2_message_set.add(message)

                    date_index += 1
                    self.message_for_owner_count[message_owners[owner_index]] = self.message_for_owner_count.get(
                        message_owners[owner_index], 0) + 1
                    owner_index += 1

    def setUp(self) -> None:
        message_test_initial_conditions(self)

    def test_valid_user_request(self):
        self.create_lists_for_different_users(page_count=1)
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])

        # owner of the related to message task
        response = self.client.get(reverse_lazy('comment-list', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 200)

        # assignee of the related to message task
        response = self.client.get(reverse_lazy('comment-list', kwargs={'pk': self.task2.id}))
        self.assertEqual(response.status_code, 200)

    def test_bad_user_request(self):
        self.create_lists_for_different_users(page_count=1)
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])

        response = self.client.get(reverse_lazy('comment-list', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_request(self):
        self.create_lists_for_different_users(page_count=1)
        response = self.client.get(reverse_lazy('comment-list', kwargs={'pk': self.task1.id}), follow=True)
        self.assertEqual(response.redirect_chain[0],
                         ("/accounts/login/?next=/task/{}/message/".format(self.task1.id), 302))

    def test_pagination(self):
        self.create_lists_for_different_users(page_count=PAGE_COUNT)
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])
        page_count = 1

        while True:
            response = self.client.get(
                reverse_lazy('comment-list', kwargs={'pk': self.task1.id}) + '?page={}'.format(page_count))

            try:
                query_list = set(response.context_data['object_list'])
                self.user1_message_set.difference_update(query_list)
            except Exception:
                page_count -= 1
                break
            page_count += 1

        self.assertEqual(page_count, PAGE_COUNT)
        self.assertEqual(len(self.user1_message_set), 0)

    def test_filter_by_date(self):
        self.create_lists_for_different_users(page_count=1)
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])

        from_date = INITIAL_CREATION_DATE[1]
        till_date = INITIAL_CREATION_DATE[-2]

        response = self.client.post(reverse_lazy('comment-list', kwargs={'pk': self.task1.id}),
                                    data={'from_date': from_date, 'till_date': till_date})
        query_list = set(response.context_data['object_list'])

        self.assertEqual(len(query_list), len(INITIAL_CREATION_DATE) - 2)

        for message in query_list:
            self.assertTrue(till_date >= message.creation_date >= from_date)


class MessageDetailTestCase(TestCase):
    def setUp(self) -> None:
        message_test_initial_conditions(self)
        self.message = Message.objects.create(body="test message",
                                              owner=self.user1,
                                              task=self.task1)

    def get_url(self):
        self.pk = Message.objects.get(body__exact="test message", owner__exact=self.user1,
                                      task__exact=self.task1).id
        return reverse_lazy('comment-detail', kwargs={'pk': self.pk})

    def test_unauthorized_user(self):
        response = self.client.get(self.get_url(), follow=True)
        self.assertEqual(response.redirect_chain[0], ('/accounts/login/?next=/message/{}/'.format(self.pk), 302))

    def test_bad_user_try_get_message(self):
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_valid_user_get_message(self):
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['message'].id, self.pk)


class MessageCreateTestCase(TestCase):
    def setUp(self) -> None:
        message_test_initial_conditions(self)

    def test_owner_and_task_assign_into_message_automatically(self):
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])
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
        message_test_initial_conditions(self)
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
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])

        response = self.get_response('message-update')
        self.assertEqual(response.status_code, 403)

        response = self.get_response('message-delete')
        self.assertEqual(response.status_code, 403)

    def test_valid_user_request(self):
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])

        response = self.get_response('message-update')
        self.assertEqual(response.redirect_chain[0],
                         (reverse_lazy('comment-detail', kwargs={'pk': self.message.id}), 302))

        response = self.get_response('message-delete')
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('comment-list', kwargs={'pk': self.task1.id}), 302))
