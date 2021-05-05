from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='chat-index'),
    path('<str:room_name>/', views.room, name='chat-room'),
    path('room/',include(
        [path('create/',views.CreateChatRoomView.as_view(),name='create-room')]
    ))
]
