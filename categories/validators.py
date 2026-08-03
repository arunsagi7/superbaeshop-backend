import os

from django.utils.text import slugify


def upload_to_title_images(instance, filename):
    basename, file_extension = os.path.splitext(filename)
    slug = slugify(instance.title)
    folder_name = slugify(instance.__class__.__name__)

    file_extension = file_extension if file_extension else ".jpg"

    new_filename = "%s%s" % (slug, file_extension)

    return "categories/%s/%s/%s" % (folder_name, slug, new_filename)
