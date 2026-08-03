from django.contrib import admin
from django.contrib.auth.models import User

from categories.admin import my_admin_site


@admin.register(User, site=my_admin_site)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "first_name", "is_staff", "is_active", "date_joined")
    list_filter = ("is_staff", "is_active", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    date_hierarchy = "date_joined"
    
    def has_delete_permission(self, request, obj=None):
        return False
