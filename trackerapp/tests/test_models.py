import os
from sqlite3.dbapi2 import Date

from django.contrib.auth.models import User
from django.test import TestCase
from django.test import override_settings

from tasktracker import settings
from ..models import UserProfile, TaskModel, Message, Attachment

TEST_MEDIA_PATH = os.path.join(settings.BASE_DIR, "test-media")
TEST_PICTURE_PATH = "assets/legion_thumbnail.jpeg"
OWNER_EMAIL = "owner@a.b"
ASSIGNEE_EMAIL = "assignee@a.b"


def create_models():
    owner = User.objects.create(first_name="Bob", last_name="Big", username="Ali", email=OWNER_EMAIL)
    UserProfile.objects.create(owner=owner, picture=TEST_PICTURE_PATH)
    assignee = User.objects.create(first_name="Bil", last_name="Small", username="Baba", email=ASSIGNEE_EMAIL)

    task = TaskModel.objects.create(title="test title",
                                    description="test description",
                                    owner=owner,
                                    assignee=assignee)

    Message.objects.create(body="test message body", owner=owner, task=task)

    Attachment.objects.create(owner=owner,
                              task=task,
                              description="test attachment description",
                              file=TEST_PICTURE_PATH)


class UserProfileTestCase(TestCase):

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def setUp(self) -> None:
        create_models()

    def test_user_profile_owner(self):
        bob = User.objects.get(id=1)
        bob_profile = UserProfile.objects.get(id=1)
        self.assertEqual(bob, bob_profile.get_owner(), msg="incorrect profile owner")

    def test_profile_has_picture(self):
        self.assertTrue(UserProfile.objects.get(id=1).picture)

    def test_profile_delete_picture(self):
        try:
            UserProfile.objects.get(id=1).picture.delete()
            self.assertTrue(not UserProfile.objects.get(id=1).picture)
        except:
            self.assertTrue(False, 'Something went wrong in the test. This warning is from "except" block')

    def test_save_method(self):
        pass


class TaskModelTestCase(TestCase):
    def setUp(self) -> None:
        create_models()

    def test_absolute_url(self):
        self.assertEqual(TaskModel.objects.get(id=1).get_absolute_url(), "/task/1/")

    def test_get_owner(self):
        self.assertEqual(TaskModel.objects.get(id=1).get_owner(), User.objects.get(email__exact=OWNER_EMAIL))

    def test_get_assignee(self):
        self.assertEqual(TaskModel.objects.get(id=1).get_assignee(), User.objects.get(email__exact=ASSIGNEE_EMAIL))

    def test_default_status(self):
        self.assertEqual(TaskModel.objects.get(id=1).status, "waiting to start")

    def test_creation_date_is_today(self):
        self.assertEqual(TaskModel.objects.get(id=1).creation_date, Date.today())


class MessageTestCase(TestCase):
    def setUp(self) -> None:
        create_models()

    def test_get_absolute_url(self):
        self.assertEqual(Message.objects.get(id=1).get_absolute_url(), "/message/1/")

    def test_get_owner(self):
        self.assertEqual(Message.objects.get(id=1).get_owner(), User.objects.get(email__exact=OWNER_EMAIL))

    def test_get_assignee(self):
        self.assertEqual(Message.objects.get(id=1).get_assignee(), User.objects.get(email__exact=ASSIGNEE_EMAIL))


class AttachmentTestCase(TestCase):
    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def setUp(self) -> None:
        create_models()
