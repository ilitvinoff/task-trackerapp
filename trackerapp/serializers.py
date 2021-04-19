import re

from coreschema.formats import validate_email
from django.contrib.auth import password_validation
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from trackerapp.models import TaskModel, Message, UserProfile, Attachment, PROFILE_IMG_UPLOAD_TO
from trackerapp.resize_img import resize

USERNAME_PATTERN = '^(?=[a-zA-Z0-9._]{8,20}$)(?!.*[_.]{2})[^_.].*[^_.]$'


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
    profile_id = serializers.ReadOnlyField(source="id")
    queryset = UserProfile.objects.all()

    def validate_picture(self, new_picture):
        previous_picture = UserProfile.objects.get(id=self.instance.id).picture

        if new_picture and (not previous_picture or new_picture.name != previous_picture.name):
            return resize(new_picture)
        return new_picture

    class Meta:
        model = UserProfile
        fields = (
            "profile_id",
            "userprofile_owner",
            "picture",
        )


class UserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=30, min_length=6, allow_blank=False, trim_whitespace=True, source= "owner.username")
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    email = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all(), message='email already taken')],source="owner.email")
    picture = serializers.ImageField(required=False, allow_null=True, use_url=PROFILE_IMG_UPLOAD_TO)

    def validate_email(self, value):
        validate_email(value)
        return value

    def validate_username(self, value):
        if re.match(USERNAME_PATTERN, value):
            return value
        raise serializers.ValidationError('plz use letters with (if want) digits to create username')

    def validate_picture(self, new_picture):
        previous_picture = UserProfile.objects.get(id=self.instance.id).picture

        if new_picture and (not previous_picture or new_picture.name != previous_picture.name):
            return resize(new_picture)
        return new_picture

    def create(self, validated_data):
        password1 = validated_data.get('password1', '')
        password2 = validated_data.get('password2', '')

        if password1 == password2:
            password_validation.validate_password(password1, self.instance)
        else:
            raise serializers.ValidationError('the passwords values do not match')

        user = User.objects.create_user(
            username=validated_data['owner']['username'],
            email=validated_data['owner']['email'],
            password=validated_data['password1'],
        )
        try:
            profile = UserProfile.objects.create(owner=user)
        except Exception as e:
            user.delete()
            raise Exception(e)

        return profile

    class Meta:
        model = UserProfile
        # Tuple of serialized model fields (see link [2])
        fields = ("username", "password1", "password2", "email", "picture")
