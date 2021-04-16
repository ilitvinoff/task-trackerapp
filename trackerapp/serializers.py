from django.contrib.auth.models import User, Group
from rest_framework import serializers

from trackerapp.models import TaskModel, Message, UserProfile, Attachment


class UserSerializer(serializers.ModelSerializer):
    owned_tasks = serializers.PrimaryKeyRelatedField(
        many=True, queryset=TaskModel.objects.all()
    )
    assigned_tasks = serializers.PrimaryKeyRelatedField(
        many=True, queryset=TaskModel.objects.all()
    )

    class Meta:
        model = User
        fields = ("id", "username", "groups", "owned_tasks", "assigned_tasks")


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ("id", "name")


class TaskSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    assignee = serializers.ReadOnlyField(source="assignee.username")

    class Meta:
        model = TaskModel
        fields = ("id", "title", "description", "owner", "assignee", "creation_date")


class MessageSerializer(serializers.ModelSerializer):
    task_id = serializers.ReadOnlyField(source="task.id")
    message_owner = serializers.ReadOnlyField(source="owner.username")
    task_owner = serializers.ReadOnlyField(source="task.owner.username")
    task_assigned_to = serializers.ReadOnlyField(source="task.assignee.username")

    class Meta:
        model = Message
        fields = (
            "id",
            "body",
            "task_id",
            "message_owner",
            "task_owner",
            "task_assigned_to",
            "creation_date",
        )


class AttachmentSerializer(serializers.ModelSerializer):
    task_id = serializers.ReadOnlyField(source="task.id")
    userprofile_owner = serializers.ReadOnlyField(source="owner.username")
    userprofile_owner_id = serializers.ReadOnlyField(source="owner.id")
    related_task_assignee = serializers.ReadOnlyField(source="task.assignee.username")
    related_task_assignee_id = serializers.ReadOnlyField(source="task.assignee.id")

    class Meta:
        model = Attachment
        fields = (
            "id",
            "userprofile_owner",
            "userprofile_owner_id",
            "related_task_assignee",
            "related_task_assignee_id",
            "description",
            "creation_date",
            "task_id",
            "file",
        )


class ProfileSerializer(serializers.ModelSerializer):
    userprofile_owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "userprofile_owner",
            "picture",
        )
