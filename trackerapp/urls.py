"""
Define urls that are related to task-tracker application
"""
from django.conf.urls import url
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

    # url(r"^signup$", views.sign_up, name="sign-up"),
    # # urls to edit/create tasks
    # url(r"task/(?P<pk>\d+)/delete$", views.TaskDelete.as_view(), name="delete-task"),
    # url(r"task/create$", views.TaskCreate.as_view(), name="create-task"),
    # url(r"task/(?P<pk>\d+)/update$", views.TaskUpdate.as_view(), name="update-task"),
    # url(
    #     r"task/(?P<pk>\d+)/status-update$",
    #     views.TaskStatusUpdate.as_view(),
    #     name="update-task-status",
    # ),
    # # user profile urls
    # url(
    #     r"user-profile/(?P<pk>\d+)$",
    #     views.UserProfileDetail.as_view(),
    #     name="user-profile-detail",
    # ),
    # url(
    #     r"user-profile/(?P<pk>\d+)/update$",
    #     views.UserProfileUpdate.as_view(),
    #     name="user-profile-update",
    # ),
    # # urls to manipulate with comments
    # url(
    #     r"task/(?P<pk>\d+)/meassage/create$",
    #     views.MessageCreate.as_view(),
    #     name="message-create",
    # ),
    # url(r"message/(?P<pk>\d+)$", views.MessageDetail.as_view(), name="comment-detail"),
    # url(
    #     r"message/(?P<pk>\d+)/delete$",
    #     views.MessageDelete.as_view(),
    #     name="message-delete",
    # ),
    # url(
    #     r"message/(?P<pk>\d+)/update$",
    #     views.MessageUpdate.as_view(),
    #     name="message-update",
    # ),
    # url(
    #     r"task/(?P<pk>\d+)/messagelist$",
    #     views.MessageListView.as_view(),
    #     name="comment-list",
    # ),
    # task's attachments urls
    url(
        r"attachment/(?P<pk>\d+)$",
        views.AttachmentDetail.as_view(),
        name="attach-detail",
    ),
    url(
        r"task/(?P<pk>\d+)/attachments$",
        views.AttachmentList.as_view(),
        name="attach-list",
    ),
    url(
        r"task/(?P<pk>\d+)/attachment/create$",
        views.AttachmentCreate.as_view(),
        name="attach-create",
    ),
    url(
        r"attachment/(?P<pk>\d+)/update$",
        views.AttachmentUpdate.as_view(),
        name="attach-update",
    ),
    url(
        r"attachment/(?P<pk>\d+)/delete$",
        views.AttachmentDelete.as_view(),
        name="attach-delete",
    ),
]
