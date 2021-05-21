from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy

from chat.models import ChatRoomModel

USER1_CREDENTIALS = ('user1', '12Asasas12', "shwonder@a.com")
USER2_CREDENTIALS = ('user2', '12Asasas12', "sharikoff@a.com")
HACKER_CREDENTIALS = ('hacker', '12test12', "hacker@b.b")
ITEMS_COUNT_IN_LIST = 10


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


class ChatRoomCreateTest(TestCase):
    def setUp(self) -> None:
        initial_test_conditions(self)

    def test_valid_user_create_room(self):
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])
        data = {'name': 'test_room', 'is_private': False}
        response = self.client.post(reverse_lazy("create-room"), data=data, follow=True)
        room_id = ChatRoomModel.objects.get(name=data['name']).id
        self.assertEqual(response.redirect_chain[0], (reverse_lazy("chat-room", kwargs={'pk': room_id}), 302))

    def test_unauthorized_user_create_room(self):
        data = {'name': 'test_room', 'is_private': False}
        response = self.client.post(reverse_lazy("create-room"), data=data, follow=True)
        self.assertEqual(response.redirect_chain[0], ('/accounts/login/?next=/chat/room/create/', 302))


class ListChatRoomViewTestCase(TestCase):
    def setUp(self) -> None:
        initial_test_conditions(self)

        for i in range(ITEMS_COUNT_IN_LIST):
            if i % 2 == 0:
                room = ChatRoomModel.objects.create(name=str(i), is_private=True, owner=self.user1)
                room.save()
                room.member.set((self.user2,))
                room.save()
            else:
                room = ChatRoomModel.objects.create(name=str(i), is_private=True, owner=self.user2)
                room.save()

    def test_valid_user_get_room_list(self):
        self.client.login(username=USER1_CREDENTIALS[0], password=USER1_CREDENTIALS[1])
        response = self.client.get(reverse_lazy("room-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), ITEMS_COUNT_IN_LIST / 2)

        self.client.login(username=USER2_CREDENTIALS[0], password=USER2_CREDENTIALS[1])
        i = 1
        user2_room_list = []
        while (True):
            response = self.client.get(reverse_lazy("room-list") + "?page={}".format(i))
            i += 1
            if response.status_code == 404:
                break
            self.assertEqual(response.status_code, 200)
            user2_room_list.extend(list(response.context['object_list']))

        self.assertEqual(len(user2_room_list), ITEMS_COUNT_IN_LIST)

    def test_unauthorized_user_request(self):
        response = self.client.get(reverse_lazy("room-list"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse_lazy("login") + "?next=/chat/room/")
