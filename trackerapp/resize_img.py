import os
from copy import deepcopy

from django.core.files import File
from stdimage import StdImageField
from PIL import Image
from io import BytesIO

MAX_WIDTH, MAX_HEIGHT = 250, 250


def resize(image: StdImageField):
    width_size = MAX_WIDTH
    height_size = MAX_HEIGHT

    im = Image.open(image)
    if im.size[0] < im.size[1]:
        height_percent = (MAX_HEIGHT / float(im.size[1]))
        width_size = int((float(im.size[0]) * float(height_percent)))
    else:
        width_percentage = (MAX_WIDTH / float(im.size[0]))
        height_size = int((float(im.size[1]))*float(width_percentage))

    im.convert('RGB')  # convert mode
    im.thumbnail((width_size, height_size))  # resize image
    thumb_io = BytesIO()  # create a BytesIO object
    im.save(thumb_io, 'JPEG', quality=85)  # save image to BytesIO object
    thumbnail = File(thumb_io, name=image.name)  # create a django friendly File object

    return thumbnail