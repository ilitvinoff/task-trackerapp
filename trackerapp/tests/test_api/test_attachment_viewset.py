import os

from django.utils import timezone
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

from tasktracker import settings
from trackerapp.views import ITEMS_ON_PAGE
from ..test_attachment import attachment_test_initial_conditions, remove_test_media_dir, \
    create_lists_for_different_users

TEST_MEDIA_PATH = os.path.join(settings.BASE_DIR, "test-media")
USER1_CREDENTIALS = ('user1', '12Asasas12', "shwonder@a.com")
USER2_CREDENTIALS = ('user2', '12Asasas12', "sharikoff@a.com")
HACKER_CREDENTIALS = ('hacker', '12test12', "hacker@b.b")

PAGE_COUNT = 5
INITIAL_CREATION_DATE = sorted([timezone.now() - timezone.timedelta(days=i) for i in range(0, ITEMS_ON_PAGE)])
DEFAULT_STATUS = "waiting to start"

TEST_FILE_PATH = 'assets/1920x1080_legion.jpg'
TEST_PATH_FOR_UPDATE_FILE = 'assets/200x200_legion.jpg'


class AttachmentViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        attachment_test_initial_conditions(self)

    def tearDown(self) -> None:
        remove_test_media_dir()

    def test_valid_user_request(self):
        create_lists_for_different_users(self, page_count=1)
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])

        # owner of the related to attachment task
        response = self.client.get(reverse_lazy('task-attachment-list-api', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 200)

        # assignee of the related to attachment task
        response = self.client.get(reverse_lazy('task-attachment-list-api', kwargs={'pk': self.task2.id}))
        self.assertEqual(response.status_code, 200)

    def test_bad_user_request(self):
        create_lists_for_different_users(self, page_count=1)
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])

        response = self.client.get(reverse_lazy('task-attachment-list-api', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_request(self):
        create_lists_for_different_users(self, page_count=1)
        response = self.client.get(reverse_lazy('task-attachment-list-api', kwargs={'pk': self.task1.id}), follow=True)
        self.assertEqual(response.status_code, 403)

    def test_pagination(self):
        create_lists_for_different_users(self, page_count=PAGE_COUNT)
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])
        page_count = 1

        while True:
            response = self.client.get(
                reverse_lazy('task-attachment-list-api', kwargs={'pk': self.task1.id}) + '?page={}'.format(page_count))

            # TODO: set(response.data['results']) - can't be done, coz response.data['results'] - is ordered dict ...
            #   implement another mechanism to compare...
            try:
                query_list = set(response.data['results'])
                self.user1_attachment_set.difference_update(query_list)
            except Exception:
                page_count -= 1
                break
            page_count += 1

        self.assertEqual(page_count, PAGE_COUNT)
        self.assertEqual(len(self.user1_attachment_set), 0)
