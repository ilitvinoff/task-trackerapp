import json
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.client import MULTIPART_CONTENT

from trackerapp.models import UserProfile

OWNER_EMAIL = "owner@a.b"
OWNER_CREDENTIALS = ('owner', '12test12')
HACKER_EMAIL = "hacker@b.b"
HACKER_CREDENTIALS = ('hacker', '12test12')


class UserProfileUpdateTest(TestCase):
    def setUp(self) -> None:
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

    def test_edit_profile_valid(self):
        self.client.login(username=OWNER_CREDENTIALS[0], password=OWNER_CREDENTIALS[1])
        data = {'first_name': 'new name'}
        # response = self.client.post("/my/form/", data, content_type="application/x-www-form-urlencoded")
        response = self.client.post(
            "/user-profile/{}/update/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id),
            data=data, follow=True)
        self.assertEqual(response.redirect_chain[0],
                         ("/user-profile/{}/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id), 302))
        self.assertEqual(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).owner.first_name, data['first_name'])

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

    # def test_picture_resized(self):
    #     self.client.login(username=OWNER_CREDENTIALS[0], password=OWNER_CREDENTIALS[1])
    #     with open('assets/200x200_legion.jpg', 'r') as img:
    #         response = self.client.put(
    #             "/user-profile/{}/update/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id),
    #             data={'first_name': 'new name', 'picture': img}, follow=True)
    #         self.assertEqual(response.redirect_chain[0], (
    #             "/user-profile/{}/".format(UserProfile.objects.get(owner__email__exact=OWNER_EMAIL).id), 302))
    #     updated_profile = UserProfile.objects.get(owner__email__exact=OWNER_EMAIL)
    #     self.assertTrue(updated_profile.picture.file, "picture is not stored to database")
    #     # saved_img = Image.open(updated_profile.picture.file)


class UserSignUpTest(TestCase):
    pass
