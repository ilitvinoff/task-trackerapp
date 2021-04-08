import os

from django.contrib.auth.models import User
from django.test import TestCase
from django.test import override_settings

from tasktracker import settings
from ..models import UserProfile

TEST_MEDIA_PATH = os.path.join(settings.BASE_DIR, "test-media")
TEST_PICTURE_PATH = "assets/legion_thumbnail.jpeg"


class UserProfileTestCase(TestCase):

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def setUp(self) -> None:
        user = User.objects.create(first_name="Bob", last_name="Big", username="Ali", email="a@b.com")

        # temp_file = tempfile.NamedTemporaryFile()
        # size = (200, 200)
        # color = (255, 0, 0, 0)
        # image = Image.new("RGB", size, color)
        # image.save(temp_file, 'jpeg')

        UserProfile.objects.create(owner=user, picture=TEST_PICTURE_PATH)  # temp_file.name)

    def test_user_profile_owner(self):
        bob = User.objects.get(id=1)
        bob_profile = UserProfile.objects.get(id=1)
        print("PATH", UserProfile.objects.get(id=1).picture.path)
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
    pass
