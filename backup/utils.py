from django.contrib.auth.models import User
from django.core import exceptions
from django.core.files.storage import default_storage

from tasktracker.exceptions import BadFileContent


def is_owner(user, instance):
    return user == instance.get_owner()


def restore_file(zip_file, file_path):
    with zip_file.open(file_path, 'r') as file:
        return default_storage.save(file.name, file)


def m2m_format(members_as_string):
    members = []

    try:
        members.extend(members_as_string[1:-1].split(','))
    except IndexError:
        raise BadFileContent(
            f"Invalid format of m2m field. Must be '[1,2,..]' - where digits are member's id. Has: '{members_as_string}'")
    res = []
    for member in members:
        try:
            res.append(int(member))
        except ValueError:
            raise BadFileContent(f"Member's ID must be digit, but has: '{member}'")
    return res


def get_user_id_by_username(username):
    if type(username) != int:
        try:
            username = username[2:-2]
        except IndexError:
            raise BadFileContent(f"Username must be in format \"['theusername']\", has instead: {username}")

        if len(username) == 0:
            raise BadFileContent(f"Username length must be greater than 0")

        try:
            return User.objects.get(username=username).id
        except User.DoesNotExist:
            raise BadFileContent(f"No user found with username '{username}'")
        except exceptions.ValidationError:
            raise BadFileContent(f"Bad username value '{username}'")

    # when username is ID
    try:
        return User.objects.get(id=username).id
    except User.DoesNotExist:
        raise BadFileContent(f"No user found with id '{username}'")
    except exceptions.ValidationError:
        raise BadFileContent(f"Bad user id value '{username}'")


def get_model_id_by_backup_id(model, backup_id):
    try:
        return model.objects.get(backup_id=backup_id).id
    except exceptions.ValidationError:
        raise BadFileContent(f"Bad backup_id value '{backup_id}' for the model '{str(model).split('.')[-1]}'")
    except model.DoesNotExist:
        raise BadFileContent(f"There is no '{str(model).split('.')[-1]}' model with backup_id value '{backup_id}'")
