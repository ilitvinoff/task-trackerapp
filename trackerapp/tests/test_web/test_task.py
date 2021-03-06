from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy

from trackerapp.models import TaskModel
from trackerapp.tests import initiators


class TaskListTestCase(TestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)
        self.task1.delete()
        self.task2.delete()

    def test_list_related_to_owner_only(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=TaskModel)

        self.client.login(username=self.user1.username, password=initiators.USER1_CREDENTIALS[1])
        response = self.client.get(reverse_lazy("index"))
        task_queryset_result = set(response.context_data['object_list'])
        self.assertSetEqual(self.user1_item_set, task_queryset_result)

    def test_pagination(self):
        initiators.create_lists_for_different_users(self, page_count=initiators.PAGE_COUNT, model_class=TaskModel)

        self.client.login(username=self.user1.username, password=initiators.USER1_CREDENTIALS[1])
        page_count = 1

        while True:
            response = self.client.get(reverse_lazy("index") + '?page={}'.format(page_count))

            try:
                query_list = set(response.context_data['object_list'])
                self.user1_item_set.difference_update(query_list)
            except Exception:
                page_count -= 1
                break
            page_count += 1

        self.assertEqual(page_count, initiators.PAGE_COUNT)
        self.assertEqual(len(self.user1_item_set), 0)

    def test_filter_options_tasks_by_date(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=TaskModel)
        self.client.login(username=self.user1.username, password=initiators.USER1_CREDENTIALS[1])

        from_date = initiators.INITIAL_CREATION_DATE[1]
        till_date = initiators.INITIAL_CREATION_DATE[-2]

        response = self.client.get(reverse_lazy("index"),
                                   data={'creation_date_after': from_date, 'creation_date_before': till_date})
        query_list = set(response.context_data['object_list'])

        self.assertEqual(len(query_list), len(initiators.INITIAL_CREATION_DATE) - 2)

        for task in query_list:
            self.assertTrue(till_date >= task.creation_date >= from_date)

    def test_filter_tasks_by_status(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=TaskModel)
        self.client.login(username=self.user1.username, password=initiators.USER1_CREDENTIALS[1])

        for current_status in range(0, len(initiators.INITIAL_STATUS)):
            response = self.client.get(reverse_lazy('index'),
                                       data={'status': initiators.INITIAL_STATUS[current_status]})
            query_list = set(response.context_data['object_list'])
            self.assertEqual(len(query_list), self.status_count[initiators.INITIAL_STATUS[current_status]])

            for task in query_list:
                self.assertEqual(task.status, initiators.INITIAL_STATUS[current_status])

    def test_assignee_list(self):
        initiators.create_lists_for_different_users(self, page_count=1, model_class=TaskModel)
        self.client.login(username=self.user2.username, password=initiators.USER2_CREDENTIALS[1])

        response = self.client.get(reverse_lazy("assigned-tasks"))
        query_list = set(response.context_data['object_list'])
        self.assertSetEqual(self.user1_item_set, query_list)


class TaskDetailTestCase(TestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def get_url(self):
        self.pk = TaskModel.objects.get(owner__email__exact=initiators.USER1_CREDENTIALS[2]).id
        return reverse_lazy('task-detail', kwargs={'pk': self.pk})

    def test_unauthorized_user(self):
        response = self.client.get(self.get_url(), follow=True)
        self.assertEqual(response.redirect_chain[0], ('/accounts/login/?next=/task/{}/'.format(self.pk), 302))

    def test_bad_user_try_get_task(self):
        self.client.login(username=self.hacker.username, password=initiators.HACKER_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 403)

    def test_valid_user_get_task(self):
        self.client.login(username=self.user1.username, password=initiators.USER1_CREDENTIALS[1])

        response = self.client.get(self.get_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context_data['taskmodel'].id, self.pk)


class TaskCreateTestCase(TestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def test_request_user_assigned_as_task_owner(self):
        self.client.login(username=self.user1.username, password=initiators.USER1_CREDENTIALS[1])
        response = self.client.post(reverse_lazy('create-task'),
                                    data={'title': 'test title', 'description': 'test_description',
                                          'status': 'waiting to start'}, follow=True)
        created_task = TaskModel.objects.filter(title__exact='test title',
                                                description__exact='test_description').first()
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('task-detail', kwargs={'pk': created_task.id}), 302))
        self.assertEqual(created_task.owner.id, self.user1.id)


class TaskUpdateDeleteTestCase(TestCase):
    def setUp(self) -> None:
        initiators.initial_test_conditions(self)

    def get_response(self, url_name):
        return self.client.post(reverse_lazy(url_name, kwargs={'pk': self.task1.id}),
                                data={'title': 'test title', 'description': 'test_description',
                                      'status': 'waiting to start'}, follow=True)

    def test_unauthorized_request(self):
        response = self.get_response('update-task')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/task/{}/update/'.format(self.task1.id), 302))

        response = self.get_response('update-task-status')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/task/{}/status-update/'.format(self.task1.id), 302))

        response = self.get_response('delete-task')
        self.assertEqual(response.redirect_chain[0],
                         ('/accounts/login/?next=/task/{}/delete/'.format(self.task1.id), 302))

    def test_bad_user_request(self):
        get_user_model().objects.create_user(username='mytko',
                                             password=initiators.USER1_CREDENTIALS[1],
                                             email='mytko@brytko.com')
        self.client.login(username='mytko', password=initiators.USER1_CREDENTIALS[1])

        response = self.get_response('update-task')
        self.assertEqual(response.status_code, 403)

        response = self.get_response("update-task-status")
        self.assertEqual(response.status_code, 403)

        response = self.get_response('delete-task')
        self.assertEqual(response.status_code, 403)

    def test_valid_user_request(self):
        self.client.login(username=self.user1.username, password=initiators.USER1_CREDENTIALS[1])

        response = self.get_response('update-task')
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('task-detail', kwargs={'pk': self.task1.id}), 302))

        response = self.get_response("update-task-status")
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('task-detail', kwargs={'pk': self.task1.id}), 302))

        response = self.get_response('delete-task')
        self.assertEqual(response.redirect_chain[0], (reverse_lazy('index'), 302))

        self.client.logout()
        self.client.login(username=self.user2.username, password=initiators.USER2_CREDENTIALS[1])
        response = self.get_response('delete-task')
        self.assertEqual(response.status_code, 403)
