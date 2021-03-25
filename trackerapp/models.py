from django.db import models
from django.contrib.auth.models import User
from django.db.models.fields import DateField, TextField, DateTimeField
from django.db.models.fields.related import ForeignKey
from django.urls import reverse


# Create your models here.


class UserProfile(models.Model):
    owner = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    picture = models.ImageField()


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

    description = TextField(
        max_length=1000, help_text="Enter a brief description of the task."
    )

    status = models.CharField(
        max_length=16,
        choices=LOAN_STATUS,
        blank=False,
        default="wS",
        help_text="Current task status",
    )

    creation_date = DateField(auto_created=True, auto_now_add=True)

    owner = ForeignKey(
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

    class Meta:
        ordering = ["creation_date", "title"]
        permissions = (("can_edit_task", "..."), ("can_change_status", "..."))


class Message(models.Model):
    body = models.CharField(max_length=1500, help_text="enter message body")

    owner = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="message_owner"
    )

    task = models.ForeignKey(TaskModel, on_delete=models.CASCADE)

    creation_date = DateTimeField(auto_created=True, auto_now_add=True)

    def get_absolute_url(self):
        """
        Returns the url to access a particular instance of the model.
        """
        return reverse("comment-detail", args=[str(self.id)])

    class Meta:
        ordering = [
            "creation_date",
        ]
