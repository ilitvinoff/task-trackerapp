import os
from io import BytesIO

from PIL import Image
from django.core.files import File
from django.db.models.fields.files import ImageFieldFile

MAX_WIDTH, MAX_HEIGHT = 250, 250


def resize(image: ImageFieldFile):
    width_size = MAX_WIDTH
    height_size = MAX_HEIGHT

    im = Image.open(image)
    thumb_io = BytesIO()  # create a BytesIO object

    # check if uploaded image need's to be resized
    if im.size[0] > MAX_WIDTH or im.size[1] > MAX_HEIGHT or (im.size[0] < MAX_WIDTH and im.size[1] < MAX_HEIGHT):

        # get coefficient from aspect ratio
        if im.size[0] < im.size[1]:
            height_percent = MAX_HEIGHT / float(im.size[1])
            width_size = int((float(im.size[0]) * float(height_percent)))
        else:
            width_percentage = MAX_WIDTH / float(im.size[0])
            height_size = int((float(im.size[1])) * float(width_percentage))

        im.convert("RGB")  # convert mode
        im.thumbnail((width_size, height_size))  # resize image
        im.save(thumb_io, "JPEG", quality=85)  # save image to BytesIO object

    im.close()
    image = File(thumb_io, name=os.path.split(image.name)[1])  # create a django friendly File object
    return image
