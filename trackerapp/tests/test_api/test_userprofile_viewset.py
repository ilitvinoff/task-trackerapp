import os
import shutil

from PIL import Image
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import override_settings
from django.urls import reverse_lazy
from rest_framework.test import APITestCase

from tasktracker import settings
from trackerapp.models import UserProfile

OWNER_CREDENTIALS = ('Ownerok', '12Asasas12', "owner@a.com")
HACKER_CREDENTIALS = ('hackerok', '12Asasas12', "hacker@b.b")
TEST_MEDIA_PATH = os.path.join(settings.BASE_DIR, "test-media")
FIRST_NAME = 'first name'
LAST_NAME = 'last name'


def get_user(user_credentials):
    return get_user_model().objects.create_user(username=user_credentials[0],
                                                password=user_credentials[1],
                                                email=user_credentials[2])


def profile_initial_conditions(self):
    self.owner = get_user(OWNER_CREDENTIALS)
    self.owner.save()

    self.test_profile = UserProfile.objects.create(owner=self.owner)
    self.test_profile.save()

    self.hacker = get_user(HACKER_CREDENTIALS)
    self.hacker.save()


class UserViewSetProfileDetailView(APITestCase):
    def setUp(self) -> None:
        profile_initial_conditions(self)

    def test_unauthorized_user(self):
        response = self.client.get(reverse_lazy("profile-api-detail", kwargs={'pk': self.test_profile.id}))
        self.assertEqual(response.status_code, 403)

    def test_get_another_profile(self):
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])
        response = self.client.get(reverse_lazy("profile-api-detail", kwargs={'pk': self.test_profile.id}))
        self.assertEqual(response.status_code, 200)

    def test_get_owned_profile(self):
        self.client.login(username=OWNER_CREDENTIALS[0], password=OWNER_CREDENTIALS[1])
        response = self.client.get(reverse_lazy("profile-api-detail", kwargs={'pk': self.test_profile.id}))
        self.assertEqual(response.status_code, 200)


class UserProfileUpdateTest(APITestCase):
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

        response = self.client.put(reverse_lazy("profile-api-detail", kwargs={'pk': self.test_profile.id}), data=data)
        self.assertEqual(response.status_code, 200)

        self.test_profile = UserProfile.objects.get(pk=self.test_profile.id)
        self.assertEqual(self.test_profile.owner.first_name, data['first_name'])
        self.assertEqual(self.test_profile.owner.last_name, data['last_name'])

    def test_edit_profile_invalid_user(self):
        self.client.login(username=HACKER_CREDENTIALS[0], password=HACKER_CREDENTIALS[1])
        data = {'first_name': 'hacker name'}
        # response = self.client.post("/my/form/", data, content_type="application/x-www-form-urlencoded")
        response = self.client.put(reverse_lazy("profile-api-detail", kwargs={'pk': self.test_profile.id}), data=data)
        self.assertEqual(response.status_code, 403)

    def test_not_authenticated_try_get_or_edit_profile(self):
        data = {'first_name': 'hacker name'}
        response = self.client.put(reverse_lazy("profile-api-detail", kwargs={'pk': self.test_profile.id}), data=data)
        self.assertEqual(response.status_code, 403)

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def test_picture_resized(self):
        self.client.login(username=OWNER_CREDENTIALS[0], password=OWNER_CREDENTIALS[1])
        with open('assets/1920x1080_legion.jpg', 'rb') as img:
            data = {'first_name': 'new name', 'last_name': 'new last name', 'picture': img}
            response = self.client.put(reverse_lazy("profile-api-detail", kwargs={'pk': self.test_profile.id}),
                                       data=data)

            self.assertEqual(response.status_code, 200)

        updated_profile = UserProfile.objects.get(owner__email__exact=OWNER_CREDENTIALS[2])
        self.assertTrue(updated_profile.picture.file, "picture is not stored to database")
        stored_img = Image.open(updated_profile.picture.file)
        expected_width_height = (250, 250)
        self.assertTrue(
            stored_img.size[0] <= expected_width_height[0] and stored_img.size[1] <= expected_width_height[1])

    @override_settings(MEDIA_ROOT=TEST_MEDIA_PATH)
    def test_fake_image_upload(self):
        self.client.login(username=OWNER_CREDENTIALS[0], password=OWNER_CREDENTIALS[1])
        with open('assets/just_text_with_img_extension.jpeg', 'rb') as img:
            previous_profile_picture_name = UserProfile.objects.get(
                owner__email__exact=OWNER_CREDENTIALS[2]).picture.name

            data = {'first_name': 'new name', 'last_name': 'new last name', 'picture': img}
            response = self.client.put(reverse_lazy("profile-api-detail", kwargs={'pk': self.test_profile.id}),
                                       data=data)

            self.assertEqual(response.status_code, 400)
            self.assertEqual(previous_profile_picture_name,
                             UserProfile.objects.get(owner__email__exact=OWNER_CREDENTIALS[2]).picture.name)


class UserSignUpTest(APITestCase):
    def test_when_valid_data(self):
        data = {
            'username': OWNER_CREDENTIALS[0],
            'email': OWNER_CREDENTIALS[2],
            'password1': OWNER_CREDENTIALS[1],
            'password2': OWNER_CREDENTIALS[1]
        }
        response = self.client.post(reverse_lazy("profile-api-list"), data=data)
        self.assertEqual(response.status_code, 201)

        created_user = User.objects.filter(email__exact=OWNER_CREDENTIALS[2]).first()
        self.assertTrue(created_user)
        self.assertEqual(created_user.username, data['username'])
        self.assertEqual(created_user.email, data['email'])

    def test_with_invalid_password(self):
        data = {
            'username': OWNER_CREDENTIALS[0],
            'email': OWNER_CREDENTIALS[2],
            'password1': 'password',
            'password2': 'password'
        }
        self.assertRaises(ValidationError, self.client.post, path=reverse_lazy("profile-api-list"), data=data)

    def test_email_already_exist(self):
        owner = get_user_model().objects.create_user(username=OWNER_CREDENTIALS[0],
                                                     password=OWNER_CREDENTIALS[1],
                                                     email=OWNER_CREDENTIALS[2])
        owner.save()

        data = {
            'username': HACKER_CREDENTIALS[0],
            'email': OWNER_CREDENTIALS[2],
            'password1': OWNER_CREDENTIALS[1],
            'password2': OWNER_CREDENTIALS[1]
        }
        response = self.client.post(reverse_lazy("profile-api-list"), data=data)
        created_user = User.objects.filter(email__exact=OWNER_CREDENTIALS[2]).last()
        self.assertFalse(created_user.username == HACKER_CREDENTIALS[0])
        self.assertEqual(response.status_code, 400)
