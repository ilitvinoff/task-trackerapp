from django.urls import path

from backup.export import export

urlpatterns = [
    path("export/", export, name="export-backup")
]
