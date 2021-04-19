"""tasktracker URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLConf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from django.urls import path
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from trackerapp import apiviews
from trackerapp.apiviews import AttachmentViewSet, MessageViewSet
from .yasg import urlpatterns as yasg_urls

router = routers.DefaultRouter()
router.register(r"profiles", apiviews.ProfileViewSet,basename='profile-api')
router.register(r"groups", apiviews.GroupViewSet,basename='group-api')
router.register(r"tasks", apiviews.TaskViewSet,basename='task-api')
router.register(r"comments", apiviews.MessageViewSet,basename='message-api')
router.register(r"attachments", apiviews.AttachmentViewSet,basename='attachment-api')

urlpatterns = [
    # WEB INTERFACE URLS

    path("", include("trackerapp.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),

    # REST API URLS
    path("api/", include([
        path('', include(router.urls)),
        path('task/<pk>/attachments/', AttachmentViewSet.as_view({'get': 'list'}),name='task-attachment-list-api'),
        path('task/<pk>/messages/', MessageViewSet.as_view({'get': 'list'}),name='task-message-list-api'),
        path("auth/", include("rest_framework.urls", namespace="rest_framework")),
        path("token/", include([
            path("", TokenObtainPairView.as_view(), name="token_obtain_pair"),
            path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
        ]))
    ])),
]

urlpatterns += yasg_urls
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
