from django.conf.urls import url
from . import views


urlpatterns = [
    # urls for task's views
    url('^$', views.TaskListView.as_view(), name='index'),
    url(r'^tasks$', views.TaskListView.as_view(), name='tasks'),
    url(r'^assigned$', views.AssigneeTaskListView.as_view(), name='assigned-tasks'),
    url(r'^task/(?P<pk>\d+)$', views.task_detail, name='task-detail'),
    # sign up view
    url(r'^signup$', views.sign_up, name='sign-up'),
    # urls to edit/create tasks
    url(r'task/(?P<pk>\d+)/delete$', views.TaskDelete.as_view(), name='delete-task'),
    url(r'task/create$', views.TaskCreate.as_view(), name='create-task'),
    url(r'task/(?P<pk>\d+)/update$', views.TaskUpdate.as_view(), name='update-task'),
    url(r'task/(?P<pk>\d+)/status-update$',
        views.TaskStatusUpdate.as_view(), name='update-task-status'),
]
