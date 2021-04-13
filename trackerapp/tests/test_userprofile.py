import os
import shutil

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse_lazy

from tasktracker import settings
from trackerapp.models import UserProfile

OWNER_EMAIL = "owner@a.b"
OWNER_CREDENTIALS = ('owner', '12test12')
HACKER_EMAIL = "hacker@b.b"
HACKER_CREDENTIALS = ('hacker', '12test12')
TEST_MEDIA_PATH = os.path.join(settings.BASE_DIR, "test-media")


def profile_initial_conditions(self):
    self.owner = get_user_model().objects.create_user(username=OWNER_CREDENTIALS[0],
                                                      password=OWNER_CREDENTIALS[1],
                                                      email=OWNER_EMAIL)
    self.owner.save()

    self.test_profile = UserProfile(owner=self.owner)
    self.test_profile.save()

    self.hacker = get_user_model().objects.create_user(username=HACKER_CREDENTIALS[0],
                                                       password=HACKER_CREDENTIALS[1],
                                                       email=HACKER_EMAIL)
    self.hacker.save()


class UserProfileDetailView(TestCase):
    def setUp(self) -> None:
        profile_initial_conditions(self)

    def test_unauthorized_user(self):
        response = self.client.get(reverse_lazy("user-profile-detail", kwargs={
            'pk': UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id}), follow=True)
        self.assertEqual(response.redirect_chain[0], ("/accounts/login/?next=/user-profile/{}/".format(
            UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id),302))

    def test_get_wrong_profile(self):
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])
        response = self.client.get(
            "/user-profile/{}/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id))
        self.assertEqual(response.status_code, 403)

    def test_get_owned_profile(self):
        self.client.login(username=OWNER_CREDENTIALS[0], password=OWNER_CREDENTIALS[1])
        response = self.client.get(
            "/user-profile/{}/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id))
        self.assertEqual(response.status_code, 200)


class UserProfileUpdateTest(TestCase):
    def setUp(self) -> None:
        profile_initial_conditions(self)

    def tearDown(self) -> None:
        if os.path.exists(TEST_MEDIA_PATH):
            try:
                shutil.rmtree(TEST_MEDIA_PATH)
            except Exception as a:
                print("ERR: CAN'T REMOVE TEST_MEDIA_DIR AFTER TEST END \n {}".format(a))

    def test_edit_profile_valid_user(self):
        self.client.login(username=OWNER_CREDENTIALS[0], password=OWNER_CREDENTIALS[1])
        data = {'first_name': 'new name', 'last_name': 'new last name'}

        response = self.client.post(
            "/user-profile/{}/update/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id),
            data=data, follow=True)
        self.assertEqual(response.redirect_chain[0],
                         ("/user-profile/{}/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id), 302))
        self.assertEqual(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).owner.first_name, data['first_name'])
        self.assertEqual(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).owner.last_name, data['last_name'])

    def test_edit_profile_invalid_user(self):
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])
        data = {'first_name': 'hacker name'}
        # response = self.client.post("/my/form/", data, content_type="application/x-www-form-urlencoded")
        response = self.client.post(
            "/user-profile/{}/update/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id),
            data=data)
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated_try_get_or_edit_profile(self):
        response = self.client.get(
            "/user-profile/{}/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id), follow=True)
        self.assertEqual(response.redirect_chain[0],
                         ("/accounts/login/?next=/user-profile/{}/".format(
                             UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id), 302))
        response = self.client.put(
            "/user-profile/{}/update/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id),
            data={'first_name': 'noname'}, follow=True)
        self.assertEqual(response.redirect_chain[0],
                         ("/accounts/login/?next=/user-profile/{}/update/".format(
                             UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id), 302))

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def test_picture_resized(self):
        self.client.login(username=OWNER_CREDENTIALS[0], password=OWNER_CREDENTIALS[1])
        with open('assets/1920x1080_legion.jpg', 'rb') as img:
            data = {'first_name': 'new name', 'last_name': 'new last name', 'picture': img}
            response = self.client.post(
                "/user-profile/{}/update/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id),
                data=data, follow=True)
            self.assertEqual(response.redirect_chain[0], (
                "/user-profile/{}/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id), 302))
        updated_profile = UserProfile.objects.get(owner__email__exact=OWNER_EMAIL)
        self.assertTrue(updated_profile.picture.file, "picture is not stored to database")
        stored_img = Image.open(updated_profile.picture.file)
        expected_width_height = (250, 250)
        self.assertTrue(
            stored_img.size[0] <= expected_width_height[0] and stored_img.size[1] <= expected_width_height[1])

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def test_fake_image_upload(self):
        self.client.login(username=OWNER_CREDENTIALS[0], password=OWNER_CREDENTIALS[1])
        with open('assets/just_text_with_img_extension.jpeg', 'rb') as img:
            previous_profile_picture_name = UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).picture.name
            data = {'first_name': 'new name', 'last_name': 'new last name', 'picture': img}
            response = self.client.post(reverse_lazy("user-profile-update", kwargs={
                'pk': UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id}), data=data, follow=True)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(previous_profile_picture_name,
                             UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).picture.name)


class UserSignUpTest(TestCase):
    pass
