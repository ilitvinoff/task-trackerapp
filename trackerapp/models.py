from django.db import models
from django.contrib.auth.models import User
from django.db.models.fields import DateField, TextField
from django.db.models.fields.related import ForeignKey
from django.urls import reverse

# Create your models here.


class TaskModel(models.Model):
    title = models.CharField(
        max_length=200, help_text="Enter title of your task)")

    description = TextField(
        max_length=1000, help_text="Enter a brief description of the task.")

    LOAN_STATUS = (
        ('wS', 'waiting to start'),
        ('iW', 'in work'),
        ('c', 'completed')
    )

    status = models.CharField(max_length=2, choices=LOAN_STATUS,
                              blank=False, default='wS', help_text='Current task status')

    creation_date = DateField(
        auto_created=True, auto_now_add=True)

    owner = ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=False)

    assignee = models.ManyToManyField(
        User, help_text="Select a user who can watch / edit / complete the task", related_name='assignee', blank=True)

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.)
        """
        return self.title

    def get_absolute_url(self):
        """
        Returns the url to access a particular instance of the model.
        """
        return reverse('task-detail', args=[str(self.id)])

    class Meta:
        ordering = ['creation_date', 'title']
        permissions = (('can_edit_task', '...'), ('can_change_status', '...'))
