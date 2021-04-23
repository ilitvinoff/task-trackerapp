"""
Define urls that are related to task-tracker application
"""
from django.urls import include, path

from . import views

urlpatterns = [
    # urls for task's views
    path("", views.TaskListView.as_view(), name="index"),

    # sign up view
    path(r"signup/", views.sign_up, name="sign-up"),

    path("task/", include([
        path("assigned/", views.AssigneeTaskListView.as_view(), name="assigned-tasks"),
        path("create/", views.TaskCreate.as_view(), name="create-task"),
        path("<pk>/", include([
            path('', views.TaskDetail.as_view(), name="task-detail"),
            path("delete/", views.TaskDelete.as_view(), name="delete-task"),
            path("update/", views.TaskUpdate.as_view(), name="update-task"),
            path("status-update/", views.TaskStatusUpdate.as_view(), name="update-task-status"),
            path("message/", include([
                path("", views.MessageListView.as_view(), name="comment-list"),
                path("create/", views.MessageCreate.as_view(), name="message-create")
            ])),
            path("attachment/", include([
                path("", views.AttachmentList.as_view(), name="attach-list"),
                path("create/", views.AttachmentCreate.as_view(), name="attach-create")
            ])),
            path("history/", views.TaskHistoryListView.as_view(), name="history-list")
        ]))
    ])),

    path("user-profile/", include([
        path("<pk>/", include([
            path('', views.UserProfileDetail.as_view(), name="user-profile-detail"),
            path('update/', views.UserProfileUpdate.as_view(), name="user-profile-update"),
        ]))
    ])),

    path("message/", include([
        path("<pk>/", include([
            path('', views.MessageDetail.as_view(), name="comment-detail"),
            path('delete/', views.MessageDelete.as_view(), name="message-delete"),
            path('update/', views.MessageUpdate.as_view(), name="message-update"),
        ]))
    ])),

    path("attachment/", include([
        path("<pk>/", include([
            path("", views.AttachmentDetail.as_view(), name="attach-detail", ),
            path("update/", views.AttachmentUpdate.as_view(), name="attach-update", ),
            path("delete/", views.AttachmentDelete.as_view(), name="attach-delete", ),
        ]))
    ])),
]
