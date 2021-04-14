import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy
from freezegun import freeze_time

from trackerapp.models import TaskModel, Message
from trackerapp.views import ITEMS_ON_PAGE

USER1_CREDENTIALS = ('shwonder', '12Asasas12', "shwonder@a.com")
USER2_CREDENTIALS = ('sharikoff', '12Asasas12', "sharikoff@a.com")
HACKER_CREDENTIALS = ('hacker', '12test12', "hacker@b.b")

PAGE_COUNT = 5
INITIAL_CREATION_DATE = sorted([datetime.date.today() - datetime.timedelta(days=i) for i in range(0, ITEMS_ON_PAGE)])
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

        for i in range(0, ITEMS_ON_PAGE * page_count * users_count):

            if date_index >= len(INITIAL_CREATION_DATE):
                date_index = 0

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
                    owner_index *= -1

    def setUp(self) -> None:
        message_test_initial_conditions(self)

    def test_valid_user_request(self):
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])

        # owner of the related to message task
        response = self.client.get(reverse_lazy('comment-list', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 200)

        # assignee of the related to message task
        response = self.client.get(reverse_lazy('comment-list', kwargs={'pk': self.task2.id}))
        self.assertEqual(response.status_code, 200)

    def test_bad_user_request(self):
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])

        # TODO: Deny permission to render empty list when request to restricted related task
        response = self.client.get(reverse_lazy('comment-list', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 403)
