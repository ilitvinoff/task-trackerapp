import os
import shutil

from django.contrib.auth import get_user_model
from django.core.files import File
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from tasktracker import settings
from trackerapp.models import TaskModel, Attachment, Message
from trackerapp.views import ITEMS_ON_PAGE

USER1_CREDENTIALS = ('user1', '12Asasas12', "shwonder@a.com")
USER2_CREDENTIALS = ('user2', '12Asasas12', "sharikoff@a.com")
HACKER_CREDENTIALS = ('hacker', '12test12', "hacker@b.b")

PAGE_COUNT = 5
INITIAL_CREATION_DATE = sorted([timezone.now() - timezone.timedelta(days=i) for i in range(0, ITEMS_ON_PAGE)])
DEFAULT_STATUS = "waiting to start"

TEST_MEDIA_PATH = os.path.join(settings.BASE_DIR, "test-media")
TEST_FILE_PATH = 'assets/1920x1080_legion.jpg'
TEST_PATH_FOR_UPDATE_FILE = 'assets/200x200_legion.jpg'
INITIAL_STATUS = ("waiting to start", "in work", "completed")


def get_user(user_credentials):
    return get_user_model().objects.create_user(username=user_credentials[0],
                                                password=user_credentials[1],
                                                email=user_credentials[2])


def initial_test_conditions(self):
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


def get_item(model_class, task, msg, owner, assignee, f, status):
    if model_class == Attachment:
        return model_class.objects.create(task=task, description=msg, file=f, owner=owner)
    elif model_class == Message:
        return model_class.objects.create(task=task, body=msg, owner=owner)
    elif model_class == TaskModel:
        return model_class.objects.create(title=msg, description=msg, owner=owner, assignee=assignee, status=status)


def create_lists_for_different_users(self, page_count, model_class):
    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def wrapper():
        self.user1_item_set = set()
        self.user2_item_set = set()
        self.status_count = {}
        owners = [self.user1, self.user2]
        users_count = len(owners)
        owner_index = 0
        date_index = 0
        status_index = 0

        with open(TEST_FILE_PATH, 'rb') as file:
            f = File(file, name='ololo')

            for i in range(0, ITEMS_ON_PAGE * page_count * users_count):

                if date_index >= len(INITIAL_CREATION_DATE):
                    date_index = 0

                if owner_index >= len(owners):
                    owner_index = 0

                if status_index >= len(INITIAL_STATUS):
                    status_index = 0

                with freeze_time(INITIAL_CREATION_DATE[date_index]):

                    if i % users_count == 0:
                        item = get_item(model_class, self.task1, str(i), owners[owner_index],
                                        owners[abs(owner_index - 1)],
                                        f, INITIAL_STATUS[status_index])
                        item.save()
                        self.user1_item_set.add(item)

                    else:
                        item = get_item(model_class, self.task2, str(i), owners[owner_index],
                                        owners[abs(owner_index - 1)],
                                        f, INITIAL_STATUS[status_index])
                        item.save()
                        self.user2_item_set.add(item)

                        date_index += 1

                        self.status_count[INITIAL_STATUS[status_index]] = self.status_count.get(
                            INITIAL_STATUS[status_index], 0) + 1
                        status_index += 1
                    owner_index += 1

    wrapper()


def remove_test_media_dir():
    if os.path.exists(TEST_MEDIA_PATH):
        try:
            shutil.rmtree(TEST_MEDIA_PATH)
        except Exception as a:
            print("ERR: CAN'T REMOVE TEST_MEDIA_DIR AFTER TEST END \n {}".format(a))


def delete_item_from_list(initial_list, item):
    for i in range(0, len(initial_list)):

        if initial_list[i]['id'] == item['id']:
            del initial_list[i]
            break


def get_initial_list(serializer_instance, item_set):
    return [serializer_instance.to_representation(item) for item in item_set]


def list_update_difference(list1, list2):
    for item in list1:
        delete_item_from_list(list2, item)
