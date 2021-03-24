from django.contrib.auth.models import User, Group
from trackerapp.models import TaskModel, Message
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class TaskSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TaskModel
        fields = ["url", "title", "owner", "assignee", "creation_date"]
        read_only_fields = [
            "owner",
        ]


class MessageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Message
        fields = ["url", "body", "task", "owner", "creation_date"]
        read_only_fields = ["owner"]
