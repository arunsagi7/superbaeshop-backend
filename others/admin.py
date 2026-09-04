from django import forms
from django.contrib import admin

from django_summernote.admin import SummernoteModelAdmin

from categories.admin import my_admin_site
from orders_management.Shipping_details import shipment_login
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


class ShipmentLoginForm(forms.ModelForm):
    class Meta:
        model = models.ShipmentLogin
        fields = "__all__"
        widgets = {
            "password": forms.PasswordInput(render_value=True),
        }


@admin.register(models.ShipmentLogin, site=my_admin_site)
class ShipmentLoginAdmin(admin.ModelAdmin):
    form = ShipmentLoginForm
    list_display = ("id", "name", "username", "is_active", "token_generated")
    fields = ("name", "username", "password", "is_active", "token")
    readonly_fields = ("token",)
    actions = ("refresh_shiprocket_token",)

    def token_generated(self, obj):
        return bool(obj.token)

    token_generated.boolean = True
    token_generated.short_description = "Token Available"

    def has_delete_permission(self, request, obj=None):
        # Only one credential record (pk=1) drives the shipping integration.
        return False

    def has_add_permission(self, request):
        # Prevent duplicates - the code always reads pk=1.
        return not models.ShipmentLogin.objects.exists()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Re-authenticate with Shiprocket immediately so the stored token is fresh.
        shipment_login()

    def refresh_shiprocket_token(self, request, queryset):
        updated = 0
        for login in queryset:
            shipment_login()
            login.refresh_from_db()
            if login.token:
                updated += 1
        self.message_user(
            request,
            "Shiprocket token refreshed for {} record(s).".format(updated),
        )

    refresh_shiprocket_token.short_description = "Refresh Shiprocket Token"


@admin.register(models.MasterHtml, site=my_admin_site)
class MasterDataAdmin(SummernoteModelAdmin):
    list_display = ("id", "title", "created_on", "is_active")
    list_filter = ("is_active",)

    def has_delete_permission(self, request, obj=None):
        return False
