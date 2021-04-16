from django.contrib.auth.models import User
from django.core.validators import validate_image_file_extension
from django.db import models
from django.urls import reverse

TASK_TITLE_MAX_LENGTH = 200
DESCRIPTION_MAX_LENGTH = 1000
DESCRIPTION_AS_TITLE_LENGTH = 40


class UserProfile(models.Model):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    picture = models.ImageField(
        upload_to="uploads/userprofile/",
        blank=True,
        null=True,
        validators=[
            validate_image_file_extension,
        ],
    )

    def get_owner(self):
        return self.owner

    # to delete previous picture override save(...)
    def save(self, *args, **kwargs):
        try:

            # check if need to clear existing profile's pic (not self.picture),
            # if new picture, - is really new (self.picture.url != profile.picture.url)
            profile = UserProfile.objects.get(id=self.id)
            if not self.picture or self.picture.url != profile.picture.url:
                previous_picture = profile.picture
                previous_picture.delete(False)

        except Exception:
            pass
        super(UserProfile, self).save(*args, **kwargs)

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.)
        """
        return self.owner.username


class TaskModel(models.Model):
    """
    Model describes task properties
    """

    # status choices
    LOAN_STATUS = (
        ("waiting to start", "waiting to start"),
        ("in work", "in work"),
        ("completed", "completed"),
    )

    title = models.CharField(max_length=TASK_TITLE_MAX_LENGTH, help_text="Enter title of your task)")

    description = models.fields.TextField(
        max_length=DESCRIPTION_MAX_LENGTH, help_text="Enter a brief description of the task."
    )

    status = models.CharField(
        max_length=16,
        choices=LOAN_STATUS,
        blank=False,
        default="waiting to start",
        help_text="Current task status",
    )

    creation_date = models.fields.DateTimeField(auto_created=True, auto_now_add=True)

    owner = models.ForeignKey(
        User,
        related_name="owned_tasks",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )

    assignee = models.ForeignKey(
        User,
        help_text="Select a user who can watch / edit / complete the task",
        related_name="assigned_tasks",
        blank=True,
        on_delete=models.SET_NULL,
        null=True,
    )

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.)
        """
        return self.title

    def get_absolute_url(self):
        """
        Returns the url to access a particular instance of the model.
        """
        return reverse("task-detail", args=[str(self.id)])

    def get_owner(self):
        return self.owner

    def get_assignee(self):
        return self.assignee

    class Meta:
        ordering = [
            "creation_date", "title"
        ]


class Message(models.Model):
    body = models.CharField(max_length=DESCRIPTION_MAX_LENGTH, help_text="enter message body")

    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="message_owner"
    )

    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE)

    creation_date = models.fields.DateTimeField(auto_created=True, auto_now_add=True)

    def get_title_from_description(self):
        return self.body[:DESCRIPTION_AS_TITLE_LENGTH] + "..."

    def get_absolute_url(self):
        """
        Returns the url to access a particular instance of the model.
        """
        return reverse("comment-detail", args=[str(self.id)])

    def get_owner(self):
        return self.owner

    def get_related_obj_owner(self):
        return self.task.owner

    def get_assignee(self):
        return self.task.assignee

    def __str__(self):
        return self.body

    class Meta:
        ordering = [
            "creation_date"
        ]


class Attachment(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="attachment_owner"
    )
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE)
    file = models.FileField(upload_to="attachments/", blank=True, null=True)
    description = models.fields.TextField(
        max_length=DESCRIPTION_MAX_LENGTH, help_text="Enter a brief description of the task."
    )

    creation_date = models.fields.DateTimeField(auto_created=True, auto_now_add=True)

    def get_absolute_url(self):
        """
        Returns the url to access a particular instance of the model.
        """
        return reverse("attach-detail", args=[str(self.id)])

    def get_title_from_description(self):
        return self.description[:DESCRIPTION_AS_TITLE_LENGTH] + "..."

    def get_owner(self):
        return self.owner

    def get_related_obj_owner(self):
        return self.task.owner

    def get_assignee(self):
        return self.task.assignee

    class Meta:
        ordering = [
            "creation_date"
        ]
