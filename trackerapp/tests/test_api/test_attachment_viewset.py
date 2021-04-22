import os

from django.core.files import File
from django.test import override_settings
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase

from .. import initiators
from ...models import Attachment
from ...serializers import AttachmentSerializer


class AttachmentListViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def tearDown(self) -> None:
        initiators.remove_test_media_dir()

    def test_valid_user_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Attachment)
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])
        initial_list = initiators.get_initial_list(AttachmentSerializer(), self.user1_item_set)

        # owner of the related to attachment task
        response = self.client.get(reverse_lazy('task-attachment-list-api', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 200)

        try:
            initiators.list_update_difference(response.data['results'], initial_list)

        except ValueError:
            self.assertFalse(True, "element of response's list not present in initial data list")

        # assignee of the related to attachment task
        response = self.client.get(reverse_lazy('task-attachment-list-api', kwargs={'pk': self.task2.id}))
        self.assertEqual(response.status_code, 200)

    def test_bad_user_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Attachment)
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.client.get(reverse_lazy('task-attachment-list-api', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Attachment)
        response = self.client.get(reverse_lazy('task-attachment-list-api', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 403)

    def test_pagination(self):
        initiators.create_lists_for_different_users(self, page_count=initiators.PAGE_COUNT, model_class=Attachment)
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])
        page_count = 1
        initial_list = initiators.get_initial_list(AttachmentSerializer(), self.user1_item_set)

        while True:
            response = self.client.get(
                reverse_lazy('task-attachment-list-api', kwargs={'pk': self.task1.id}) + '?page={}'.format(page_count))

            try:
                initiators.list_update_difference(response.data['results'], initial_list)

            except ValueError:
                self.assertFalse(True, "element of response's list not present in initial data list")
            except KeyError:
                page_count -= 1
                break
            page_count += 1

        self.assertEqual(page_count, initiators.PAGE_COUNT)
        self.assertEqual(len(initial_list), 0)


class AttachmentDetailViewSetTestCase(APITestCase):
    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)
        with open(initiators.TEST_FILE_PATH, 'rb') as file:
            f = File(file, name='attachment-file')
            self.attachment = Attachment.objects.create(description="test attachment",
                                                        file=f,
                                                        owner=self.user1,
                                                        task=self.task1)

    def tearDown(self) -> None:
        initiators.remove_test_media_dir()

    def get_url(self):
        self.pk = Attachment.objects.get(description__exact="test attachment", owner__exact=self.user1,
                                         task__exact=self.task1).id
        return reverse_lazy('attachment-api-detail', kwargs={'pk': self.pk})

    def test_unauthorized_user(self):
        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_bad_user_try_get_attachment(self):
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_valid_user_get_attachment(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.pk, "Initial obj mismatched with response obj")


class AttachmentCreateViewSetTestCase(APITestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def tearDown(self) -> None:
        initiators.remove_test_media_dir()

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def test_owner_and_task_assign_set_into_attachment_automatically(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])
        with open(initiators.TEST_FILE_PATH, 'rb') as file:
            data = {'description': 'test attachment create', 'file': file, 'task_id': self.task1.id}

            response = self.client.post(reverse_lazy('attachment-api-list'), data=data)

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.data['owner_username'], self.user1.username)
            self.assertEqual(response.data['related_task_assignee'], self.task1.assignee.username)

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def test_unauthorized_user_creation_request(self):
        with open(initiators.TEST_FILE_PATH, 'rb') as file:
            data = {'description': 'test attachment create', 'file': file, 'task_id': self.task1.id}

            response = self.client.post(reverse_lazy('attachment-api-list'), data=data)
            self.assertEqual(response.status_code, 403)


class AttachmentUpdateDeleteTestCase(APITestCase):
    def get_attachment_name(self, description, user, task):
        return Attachment.objects.get(description__exact=description,
                                      owner__exact=user,
                                      task=task).file.name

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)
        with open(initiators.TEST_FILE_PATH, 'rb') as file:
            f = File(file, name='attachment-file')
            self.attachment = Attachment.objects.create(description="test attachment",
                                                        file=f,
                                                        owner=self.user1,
                                                        task=self.task1)
        self.previous_attachment_name = self.get_attachment_name("test attachment", self.user1, self.task1)

    def tearDown(self) -> None:
        initiators.remove_test_media_dir()

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def get_update_response(self):
        with open(initiators.TEST_PATH_FOR_UPDATE_FILE, 'rb') as file:
            return self.client.put(reverse_lazy('attachment-api-detail', kwargs={'pk': self.attachment.id}),
                                   data={'description': 'new attachment description', 'file': file})

    def get_delete_response(self):
        with open(initiators.TEST_PATH_FOR_UPDATE_FILE, 'rb') as file:
            return self.client.delete(reverse_lazy('attachment-api-detail', kwargs={'pk': self.attachment.id}),
                                      data={'description': 'new attachment description', 'file': file})

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def test_unauthorized_request(self):
        response = self.get_update_response()
        self.assertEqual(response.status_code, 403)

        response = self.get_delete_response()
        self.assertEqual(response.status_code, 403)

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def test_bad_user_request(self):
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.get_update_response()
        self.assertEqual(response.status_code, 403)

        response = self.get_delete_response()
        self.assertEqual(response.status_code, 403)

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def test_valid_user_request(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        response = self.get_update_response()
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(os.path.split(self.previous_attachment_name)[1], os.path.split(response.data['file'])[1])

        response = self.get_delete_response()
        self.assertEqual(response.status_code, 204)
