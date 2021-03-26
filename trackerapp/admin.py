from django.contrib import admin
from .models import TaskModel, Message, UserProfile


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


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("body", "owner", "task", "creation_date")
    list_filter = ("owner", "task", "creation_date")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("owner", "picture")
    list_filter = ("owner",)
