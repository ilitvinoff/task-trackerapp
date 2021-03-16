from django.contrib import admin
from .models import TaskModel


@admin.register(TaskModel)
class TaskModelAdmin(admin.ModelAdmin):
    """
    Define admin panel's properties
    """
    list_display = ("title", "status", "owner", "creation_date")
    list_filter = ("owner", "status", "assignee", "creation_date")
    fieldsets = (
        (None, {"fields": ("title", "description")}),
        ("Users:", {"fields": ("owner", "assignee", "status")}),
    )
