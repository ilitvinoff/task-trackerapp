import os
import shutil

from django.contrib.auth import get_user_model
from django.core.files import File
from django.test import TestCase, override_settings
from django.urls import reverse_lazy
from django.utils import timezone
from freezegun import freeze_time

from tasktracker import settings
from trackerapp.models import TaskModel, Attachment
from trackerapp.views import ITEMS_ON_PAGE

TEST_MEDIA_PATH = os.path.join(settings.BASE_DIR, "test-media")
USER1_CREDENTIALS = ('user1', '12Asasas12', "shwonder@a.com")
USER2_CREDENTIALS = ('user2', '12Asasas12', "sharikoff@a.com")
HACKER_CREDENTIALS = ('hacker', '12test12', "hacker@b.b")

PAGE_COUNT = 5
INITIAL_CREATION_DATE = sorted([timezone.now() - timezone.timedelta(days=i) for i in range(0, ITEMS_ON_PAGE)])
DEFAULT_STATUS = "waiting to start"

TEST_FILE_PATH = 'assets/1920x1080_legion.jpg'
TEST_PATH_FOR_UPDATE_FILE = 'assets/200x200_legion.jpg'


def get_user(user_credentials):
    return get_user_model().objects.create_user(username=user_credentials[0],
                                                password=user_credentials[1],
                                                email=user_credentials[2])


def attachment_test_initial_conditions(self):
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


def create_lists_for_different_users(self, page_count):
    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def wrapper():
        self.user1_attachment_set = set()
        self.user2_attachment_set = set()
        self.attachment_for_owner_count = {}
        attachment_owners = [self.user1, self.user2]
        users_count = len(attachment_owners)
        owner_index = 1
        date_index = 0

        with open(TEST_FILE_PATH, 'rb') as file:
            f = File(file, name='ololo')

            for i in range(0, ITEMS_ON_PAGE * page_count * users_count):

                if date_index >= len(INITIAL_CREATION_DATE):
                    date_index = 0

                if owner_index >= len(attachment_owners):
                    owner_index = 0

                with freeze_time(INITIAL_CREATION_DATE[date_index]):

                    if i % users_count == 0:
                        attachment = Attachment.objects.create(task=self.task1, description=i, file=f,
                                                               owner=attachment_owners[owner_index])
                        attachment.save()
                        self.user1_attachment_set.add(attachment)

                    else:
                        attachment = Attachment.objects.create(task=self.task2, description=i, file=f,
                                                               owner=attachment_owners[owner_index])
                        attachment.save()
                        self.user2_attachment_set.add(attachment)

                        date_index += 1
                        self.attachment_for_owner_count[
                            attachment_owners[owner_index]] = self.attachment_for_owner_count.get(
                            attachment_owners[owner_index], 0) + 1
                        owner_index += 1

    wrapper()


def remove_test_media_dir():
    if os.path.exists(TEST_MEDIA_PATH):
        try:
            shutil.rmtree(TEST_MEDIA_PATH)
        except Exception as a:
            print("ERR: CAN'T REMOVE TEST_MEDIA_DIR AFTER TEST END \n {}".format(a))


class AttachmentListView(TestCase):
    def setUp(self) -> None:
        attachment_test_initial_conditions(self)

    def tearDown(self) -> None:
        remove_test_media_dir()

    def test_valid_user_request(self):
        create_lists_for_different_users(self, page_count=1)
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])

        # owner of the related to attachment task
        response = self.client.get(reverse_lazy('attach-list', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 200)

        # assignee of the related to attachment task
        response = self.client.get(reverse_lazy('attach-list', kwargs={'pk': self.task2.id}))
        self.assertEqual(response.status_code, 200)

    def test_bad_user_request(self):
        create_lists_for_different_users(self, page_count=1)
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])

        response = self.client.get(reverse_lazy('attach-list', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_request(self):
        create_lists_for_different_users(self, page_count=1)
        response = self.client.get(reverse_lazy('attach-list', kwargs={'pk': self.task1.id}), follow=True)
        self.assertEqual(response.redirect_chain[0],
                         ("/accounts/login/?next=/task/{}/attachment/".format(self.task1.id), 302))

    def test_pagination(self):
        create_lists_for_different_users(self, page_count=PAGE_COUNT)
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])
        page_count = 1

        while True:
            response = self.client.get(
                reverse_lazy('attach-list', kwargs={'pk': self.task1.id}) + '?page={}'.format(page_count))

            try:
                query_list = set(response.context_data['object_list'])
                self.user1_attachment_set.difference_update(query_list)
            except Exception:
                page_count -= 1
                break
            page_count += 1

        self.assertEqual(page_count, PAGE_COUNT)
        self.assertEqual(len(self.user1_attachment_set), 0)

    def test_filter_by_date(self):
        create_lists_for_different_users(self, page_count=1)
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])

        from_date = INITIAL_CREATION_DATE[1]
        till_date = INITIAL_CREATION_DATE[-2]

        response = self.client.post(reverse_lazy('attach-list', kwargs={'pk': self.task1.id}),
                                    data={'from_date': from_date, 'till_date': till_date})
        query_list = set(response.context_data['object_list'])

        self.assertEqual(len(query_list), len(INITIAL_CREATION_DATE) - 2)

        for attachment in query_list:
            self.assertTrue(till_date >= attachment.creation_date >= from_date)


class AttachmentDetailTestCase(TestCase):
    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def setUp(self) -> None:
        attachment_test_initial_conditions(self)
        with open(TEST_FILE_PATH, 'rb') as file:
            f = File(file, name='attachment-file')
            self.attachment = Attachment.objects.create(description="test attachment",
                                                        file=f,
                                                        owner=self.user1,
                                                        task=self.task1)

    def tearDown(self) -> None:
        remove_test_media_dir()

    def get_url(self):
        self.pk = Attachment.objects.get(description__exact="test attachment", owner__exact=self.user1,
                                         task__exact=self.task1).id
        return reverse_lazy('attach-detail', kwargs={'pk': self.pk})

    def test_unauthorized_user(self):
        response = self.client.get(self.get_url(), follow=True)
        self.assertEqual(response.redirect_chain[0], ('/accounts/login/?next=/attachment/{}/'.format(self.pk), 302))

    def test_bad_user_try_get_attachment(self):
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_valid_user_get_attachment(self):
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['attachment'].id, self.pk)


class AttachmentCreateTestCase(TestCase):
    def setUp(self) -> None:
        attachment_test_initial_conditions(self)

    def tearDown(self) -> None:
        remove_test_media_dir()

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def test_owner_and_task_assign_into_attachment_automatically(self):
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])
        with open(TEST_FILE_PATH, 'rb') as file:
            data = {'description': 'test attachment create', 'file': file}

            response = self.client.post(reverse_lazy('attach-create', kwargs={'pk': self.task1.id}), data=data,
                                        follow=True)
            created_attachment = Attachment.objects.get(description='test attachment create')
            self.assertEqual(response.redirect_chain[0],
                             (reverse_lazy('attach-detail', kwargs={'pk': created_attachment.id}), 302))
            self.assertEqual(created_attachment.owner, self.user1)
            self.assertEqual(created_attachment.task, self.task1)

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def test_unauthorized_user_creation_request(self):
        with open(TEST_FILE_PATH, 'rb') as file:
            data = {'description': 'test attachment create', 'file': file}

            response = self.client.post(reverse_lazy('attach-create', kwargs={'pk': self.task1.id}), data=data,
                                        follow=True)
            self.assertEqual(response.redirect_chain[0],
                             ('/accounts/login/?next=/task/{}/attachment/create/'.format(self.task1.id), 302))


class AttachmentUpdateDeleteTestCase(TestCase):
    def get_attachment_name(self, description, user, task):
        return Attachment.objects.get(description__exact=description,
                                      owner__exact=user,
                                      task=task).file.name

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def setUp(self) -> None:
        attachment_test_initial_conditions(self)
        with open(TEST_FILE_PATH, 'rb') as file:
            f = File(file, name='attachment-file')
            self.attachment = Attachment.objects.create(description="test attachment",
                                                        file=f,
                                                        owner=self.user1,
                                                        task=self.task1)
        self.previous_attachment_name = self.get_attachment_name("test attachment", self.user1, self.task1)

    def tearDown(self) -> None:
        remove_test_media_dir()

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def get_response(self, url_name):
        with open(TEST_PATH_FOR_UPDATE_FILE, 'rb') as file:
            return self.client.post(reverse_lazy(url_name, kwargs={'pk': self.attachment.id}),
                                    data={'description': 'new attachment description', 'file': file}, follow=True)

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def test_unauthorized_request(self):
        response = self.get_response('attach-update')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/attachment/{}/update/'.format(self.attachment.id), 302))

        response = self.get_response('attach-delete')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/attachment/{}/delete/'.format(self.attachment.id), 302))

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def test_bad_user_request(self):
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])

        response = self.get_response('attach-update')
        self.assertEqual(response.status_code, 403)

        response = self.get_response('attach-delete')
        self.assertEqual(response.status_code, 403)

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def test_valid_user_request(self):
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])

        response = self.get_response('attach-update')
        self.assertEqual(response.redirect_chain[0],
                         (reverse_lazy('attach-detail', kwargs={'pk': self.attachment.id}), 302))
        self.assertNotEqual(self.previous_attachment_name,
                            self.get_attachment_name('new attachment description', self.user1, self.task1))

        response = self.get_response('attach-delete')
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('attach-list', kwargs={'pk': self.task1.id}), 302))
