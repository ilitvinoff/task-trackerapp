from django.core.files.storage import default_storage


def is_owner(user, instance):
    return user == instance.get_owner()


def restore_file(zip_file, file_path):
    with zip_file.open(file_path, 'r') as file:
        return default_storage.save(file.name, file)
