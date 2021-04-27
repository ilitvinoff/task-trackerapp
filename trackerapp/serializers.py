from coreschema.formats import validate_email
from django.contrib.auth import password_validation
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from trackerapp.models import TaskModel, Message, UserProfile, Attachment
from trackerapp.resize_img import resize


class HistoricalRecordField(serializers.ListField):
    child = serializers.DictField()

    def to_representation(self, data):
        return super().to_representation(data.values().order_by('history_date'))


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


class TaskHistorySerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    assignee_username = serializers.ReadOnlyField(source="assignee.username")
    history = HistoricalRecordField(read_only=True)

    class Meta:
        model = TaskModel
        fields = ("owner", "assignee_username", "history")


class TaskSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    assignee_username = serializers.ReadOnlyField(source="assignee.username")

    class Meta:
        model = TaskModel
        fields = ("id", "title", "description", "owner", "assignee_username", "assignee", "status", "creation_date")
        extra_kwargs = {'assignee': {'write_only': True}}


class MessageSerializer(serializers.ModelSerializer):
    task_id = serializers.ReadOnlyField(source="task.id")
    owner = serializers.ReadOnlyField(source="owner.username")
    task_owner = serializers.ReadOnlyField(source="task.owner.username")
    task_assigned_to = serializers.ReadOnlyField(source="task.assignee.username")

    class Meta:
        model = Message
        fields = (
            "id",
            "body",
            "task_id",
            "owner",
            "task_owner",
            "task_assigned_to",
            "creation_date",
        )


class AttachmentSerializer(serializers.ModelSerializer):
    task_id = serializers.ReadOnlyField(source="task.id")
    owner_username = serializers.ReadOnlyField(source="owner.username")
    owner_id = serializers.ReadOnlyField(source="owner.id")
    related_task_assignee = serializers.ReadOnlyField(source="task.assignee.username")
    related_task_assignee_id = serializers.ReadOnlyField(source="task.assignee.id")

    class Meta:
        model = Attachment
        fields = (
            "id",
            "owner_username",
            "owner_id",
            "related_task_assignee",
            "related_task_assignee_id",
            "description",
            "creation_date",
            "task_id",
            "file",
        )


class ProfileSerializer(serializers.ModelSerializer):
    profile_owner_id = serializers.ReadOnlyField(source="owner.id")
    profile_id = serializers.ReadOnlyField(source="id")
    queryset = UserProfile.objects.all()

    def validate_picture(self, new_picture):
        previous_picture = UserProfile.objects.get(id=self.instance.id).picture

        if new_picture and (not previous_picture or new_picture.name != previous_picture.name):
            return resize(new_picture)
        return new_picture

    def save(self, **kwargs):
        request = self.context.get('request')

        if request:

            first_name = request.data.get('first_name', None)
            if first_name:
                kwargs['first_name'] = first_name

            last_name = request.data.get('last_name', None)
            if last_name:
                kwargs['last_name'] = last_name

        super(ProfileSerializer, self).save(**kwargs)

    def update(self, instance, validated_data):
        first_name = validated_data.get('first_name', None)
        last_name = validated_data.get('last_name', None)
        picture = validated_data.get('picture', None)
        previous_owner_value = instance.owner

        if first_name:
            instance.owner.first_name = first_name
        if last_name:
            instance.owner.last_name = last_name
        if picture:
            instance.picture = picture

        instance.owner.save()
        try:
            instance.save()
        except:
            instance.owner = previous_owner_value
            instance.save()

        return instance

    class Meta:
        model = UserProfile
        fields = (
            "profile_id",
            "profile_owner_id",
            "picture",
        )


class UserRegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=30, min_length=6, allow_blank=False, trim_whitespace=True,
                                     source="owner.username")
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    email = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all(), message='email already taken')], source="owner.email")

    def validate_email(self, value):
        validate_email(value)
        if User.objects.filter(email__exact=value).first():
            raise ValidationError("this email already taken")
        return value

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

        user.save()

        try:
            profile = UserProfile.objects.create(owner=user)
        except Exception as e:
            user.delete()
            raise Exception(e)

        return profile

    class Meta:
        model = UserProfile
        # Tuple of serialized model fields (see link [2])
        fields = ("username", "password1", "password2", "email")
