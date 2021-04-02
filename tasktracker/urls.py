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
from .yasg import urlpatterns as yasg_urls

from trackerapp import apiviews

router = routers.DefaultRouter()
router.register(r"users", apiviews.UserViewSet)
router.register(r"groups", apiviews.GroupViewSet)
router.register(r"tasks", apiviews.TaskViewSet)
router.register(r"comments", apiviews.MessageViewSet)

urlpatterns = [
    # WEB INTERFACE URLS

    path("", include("trackerapp.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),

    # REST API URLS
    path("api/", include([
        path('', include(router.urls)),
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
