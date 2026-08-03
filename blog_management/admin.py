from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from blog_management import models
from categories.admin import my_admin_site


@admin.register(models.Tags, site=my_admin_site)
class TagsAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(models.Authors, site=my_admin_site)
class AuthorsAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Blog, site=my_admin_site)
class BlogAdmin(SummernoteModelAdmin):
    list_display = ("id", "title", "short_description", "is_active")
    list_filter = ("author", "is_active", "tag")
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ("tag",)

    def has_delete_permission(self, request, obj=None):
        return False
