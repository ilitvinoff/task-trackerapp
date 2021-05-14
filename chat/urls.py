from django.urls import path, include

from . import views

urlpatterns = [

    path('room/', include([
        path('', views.ListChatRoomView.as_view(), name='room-list'),
        path('create/', views.CreateChatRoomView.as_view(), name='create-room'),
        path('<pk>/', include([
            path('', views.ChatRoomDetail.as_view(), name='chat-room'),
            path('delete/', views.DeleteChatRoomView.as_view(), name='delete-room'),
            path('update/', views.UpdateChatRoomView.as_view(), name='update-room'),
        ])),
    ]
    ))
]
