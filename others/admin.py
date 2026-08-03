from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from categories.admin import my_admin_site
from . import models


@admin.register(models.Newsletters, site=my_admin_site)
class NewslettersAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "created_on")
    date_hierarchy = "created_on"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(models.MasterHtml, site=my_admin_site)
class MasterDataAdmin(SummernoteModelAdmin):
    list_display = ("id", "title", "created_on", "is_active")
    list_filter = ("is_active",)

    def has_delete_permission(self, request, obj=None):
        return False
