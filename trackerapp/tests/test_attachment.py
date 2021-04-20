from django.core.files import File
from django.test import TestCase, override_settings
from django.urls import reverse_lazy

from trackerapp.models import Attachment
from . import initiators


class AttachmentListView(TestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def tearDown(self) -> None:
        initiators.remove_test_media_dir()

    def test_valid_user_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Attachment)
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        # owner of the related to attachment task
        response = self.client.get(reverse_lazy('attach-list', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 200)

        # assignee of the related to attachment task
        response = self.client.get(reverse_lazy('attach-list', kwargs={'pk': self.task2.id}))
        self.assertEqual(response.status_code, 200)

    def test_bad_user_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Attachment)
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.client.get(reverse_lazy('attach-list', kwargs={'pk': self.task1.id}))
        self.assertEqual(response.status_code, 403)

    def test_unauthorized_request(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Attachment)
        response = self.client.get(reverse_lazy('attach-list', kwargs={'pk': self.task1.id}), follow=True)
        self.assertEqual(response.redirect_chain[0],
                         ("/accounts/login/?next=/task/{}/attachment/".format(self.task1.id), 302))

    def test_pagination(self):
        initiators.create_lists_for_different_users(self, page_count=initiators.PAGE_COUNT, model_class=Attachment)
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])
        page_count = 1

        while True:
            response = self.client.get(
                reverse_lazy('attach-list', kwargs={'pk': self.task1.id}) + '?page={}'.format(page_count))

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
        initiators.create_lists_for_different_users(self, page_count=1, model_class=Attachment)
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        from_date = initiators.INITIAL_CREATION_DATE[1]
        till_date = initiators.INITIAL_CREATION_DATE[-2]

        response = self.client.post(reverse_lazy('attach-list', kwargs={'pk': self.task1.id}),
                                    data={'from_date': from_date, 'till_date': till_date})
        query_list = set(response.context_data['object_list'])

        self.assertEqual(len(query_list), len(initiators.INITIAL_CREATION_DATE) - 2)

        for attachment in query_list:
            self.assertTrue(till_date >= attachment.creation_date >= from_date)


class AttachmentDetailTestCase(TestCase):
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
        return reverse_lazy('attach-detail', kwargs={'pk': self.pk})

    def test_unauthorized_user(self):
        response = self.client.get(self.get_url(), follow=True)
        self.assertEqual(response.redirect_chain[0], ('/accounts/login/?next=/attachment/{}/'.format(self.pk), 302))

    def test_bad_user_try_get_attachment(self):
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_valid_user_get_attachment(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['attachment'].id, self.pk)


class AttachmentCreateTestCase(TestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def tearDown(self) -> None:
        initiators.remove_test_media_dir()

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def test_owner_and_task_assign_into_attachment_automatically(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])
        with open(initiators.TEST_FILE_PATH, 'rb') as file:
            data = {'description': 'test attachment create', 'file': file}

            response = self.client.post(reverse_lazy('attach-create', kwargs={'pk': self.task1.id}), data=data,
                                        follow=True)
            created_attachment = Attachment.objects.get(description='test attachment create')
            self.assertEqual(response.redirect_chain[0],
                             (reverse_lazy('attach-detail', kwargs={'pk': created_attachment.id}), 302))
            self.assertEqual(created_attachment.owner, self.user1)
            self.assertEqual(created_attachment.task, self.task1)

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def test_unauthorized_user_creation_request(self):
        with open(initiators.TEST_FILE_PATH, 'rb') as file:
            data = {'description': 'test attachment create', 'file': file}

            response = self.client.post(reverse_lazy('attach-create', kwargs={'pk': self.task1.id}), data=data,
                                        follow=True)
            self.assertEqual(response.redirect_chain[0],
                             ('/accounts/login/?next=/task/{}/attachment/create/'.format(self.task1.id), 302))


def get_attachment_name(description, user, task):
    return Attachment.objects.get(description__exact=description,
                                  owner__exact=user,
                                  task=task).file.name


class AttachmentUpdateDeleteTestCase(TestCase):

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)
        with open(initiators.TEST_FILE_PATH, 'rb') as file:
            f = File(file, name='attachment-file')
            self.attachment = Attachment.objects.create(description="test attachment",
                                                        file=f,
                                                        owner=self.user1,
                                                        task=self.task1)
        self.previous_attachment_name = get_attachment_name("test attachment", self.user1, self.task1)

    def tearDown(self) -> None:
        initiators.remove_test_media_dir()

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def get_response(self, url_name):
        with open(initiators.TEST_PATH_FOR_UPDATE_FILE, 'rb') as file:
            return self.client.post(reverse_lazy(url_name, kwargs={'pk': self.attachment.id}),
                                    data={'description': 'new attachment description', 'file': file}, follow=True)

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def test_unauthorized_request(self):
        response = self.get_response('attach-update')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/attachment/{}/update/'.format(self.attachment.id), 302))

        response = self.get_response('attach-delete')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/attachment/{}/delete/'.format(self.attachment.id), 302))

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def test_bad_user_request(self):
        self.client.login(username=initiators.HACKER_CREDENTIALS[0], password=initiators.HACKER_CREDENTIALS[1])

        response = self.get_response('attach-update')
        self.assertEqual(response.status_code, 403)

        response = self.get_response('attach-delete')
        self.assertEqual(response.status_code, 403)

    @override_settings(MEDIA_ROOT=initiators.TEST_MEDIA_PATH)
    def test_valid_user_request(self):
        self.client.login(username=initiators.USER1_CREDENTIALS[0], password=initiators.USER1_CREDENTIALS[1])

        response = self.get_response('attach-update')
        self.assertEqual(response.redirect_chain[0],
                         (reverse_lazy('attach-detail', kwargs={'pk': self.attachment.id}), 302))
        self.assertNotEqual(self.previous_attachment_name,
                            get_attachment_name('new attachment description', self.user1, self.task1))

        response = self.get_response('attach-delete')
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('attach-list', kwargs={'pk': self.task1.id}), 302))
