from django.core.validators import validate_image_file_extension
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


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
            previous_picture = UserProfile.objects.get(id=self.id).picture
            previous_picture.delete()

        except:
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

    title = models.CharField(max_length=200, help_text="Enter title of your task)")

    description = models.fields.TextField(
        max_length=1000, help_text="Enter a brief description of the task."
    )

    status = models.CharField(
        max_length=16,
        choices=LOAN_STATUS,
        blank=False,
        default="wS",
        help_text="Current task status",
    )

    creation_date = models.fields.DateField(auto_created=True, auto_now_add=True)

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
        ordering = ["creation_date", "title"]
        permissions = (("can_edit_task", "..."), ("can_change_status", "..."))


class Message(models.Model):
    body = models.CharField(max_length=1500, help_text="enter message body")

    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="message_owner"
    )

    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE)

    creation_date = models.fields.DateTimeField(auto_created=True, auto_now_add=True)

    def get_absolute_url(self):
        """
        Returns the url to access a particular instance of the model.
        """
        return reverse("comment-detail", args=[str(self.id)])

    def get_owner(self):
        return self.owner

    def get_assignee(self):
        return self.task.assignee

    def __str__(self):
        return self.body

    class Meta:
        ordering = [
            "creation_date",
        ]


class Attachment(models.Model):
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="attachment_owner")
    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE)
    file = models.FileField(upload_to="attachments/", blank=True, null=True)
    description = models.fields.TextField(
        max_length=1000, help_text="Enter a brief description of the task."
    )
    creation_date = models.fields.DateTimeField(auto_created=True, auto_now_add=True)

    def get_absolute_url(self):
        """
        Returns the url to access a particular instance of the model.
        """
        return reverse("attach-detail", args=[str(self.id)])

    def get_title_from_description(self):
        return self.description[:40] + '...'

    def get_owner(self):
        return self.owner

    def get_assignee(self):
        return self.task.assignee

    class Meta:
        ordering = [
            "creation_date",
        ]
