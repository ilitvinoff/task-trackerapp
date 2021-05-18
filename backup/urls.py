from django.urls import path

from backup.export import export
from backup.import_backup import import_backup

urlpatterns = [
    path("export/", export, name="export-backup"),
    path("import/", import_backup, name="import-backup")
]
