import os

from django.db import models
from django.utils.text import slugify


def upload_to_photos(instance, filename):
    basename, file_extension = os.path.splitext(filename)

    slug = slugify(instance.title)

    new_filename = "%s%s" % (slug, file_extension)
    return "%s/%s" % (instance.__class__.__name__, new_filename)


class Tags(models.Model):
    objects = None
    name = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "tbl_blog_tags"
        verbose_name = "Blog Tag"
        verbose_name_plural = "Blog Tags"

    def __str__(self):
        return self.name


class Authors(models.Model):
    objects = None
    name = models.CharField(max_length=60, unique=True)
    description = models.CharField(max_length=120, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    profile_pic = models.ImageField(upload_to="blog-image/author")

    class Meta:
        db_table = "tbl_author"
        verbose_name = "Author"
        verbose_name_plural = "Authors"

    def __str__(self):
        return self.name


class Blog(models.Model):
    objects = None
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField()
    short_description = models.CharField(max_length=254)
    date = models.DateField()
    description = models.TextField()
    image = models.ImageField(upload_to=upload_to_photos)
    is_active = models.BooleanField(default=False)
    tag = models.ManyToManyField(Tags, blank=True)
    author = models.ForeignKey(Authors, on_delete=models.CASCADE)
    meta_keyword = models.CharField(max_length=256, blank=True, null=True)
    meta_description = models.TextField(max_length=600, blank=True, null=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_blog"
        verbose_name = "Blog"
        verbose_name_plural = "Blog"

    def __str__(self):
        return self.title
