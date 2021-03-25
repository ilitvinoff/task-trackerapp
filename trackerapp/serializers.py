from django.contrib.auth.models import User, Group
from trackerapp.models import TaskModel, Message
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    owned_tasks = serializers.PrimaryKeyRelatedField(
        many=True, queryset=TaskModel.objects.all()
    )
    assigned_tasks = serializers.PrimaryKeyRelatedField(
        many=True, queryset=TaskModel.objects.all()
    )

    class Meta:
        model = User
        fields = ["url", "username", "groups", "owned_tasks", "assigned_tasks"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class TaskSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    assignee = serializers.ReadOnlyField(source="assignee.username")

    class Meta:
        model = TaskModel
        fields = ["url", "title", "description", "owner", "assignee", "creation_date"]


class MessageSerializer(serializers.HyperlinkedModelSerializer):
    message_owner = serializers.ReadOnlyField(source="owner.username")
    task_owner = serializers.ReadOnlyField(source="task.owner.username")
    task_assigned_to = serializers.ReadOnlyField(source="task.assignee.username")

    class Meta:
        model = Message
        fields = [
            "url",
            "body",
            "task",
            "message_owner",
            "task_owner",
            "task_assigned_to",
            "creation_date",
        ]
