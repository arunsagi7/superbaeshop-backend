import csv

from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from cart_management import models
from categories.admin import my_admin_site
from orders_management.models import Orders


@admin.register(models.Cart, site=my_admin_site)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user_details", "product", "quantity", "created_on")
    date_hierarchy = "created_on"
    change_list_template = "cart_list_template.html"
    list_filter = ("product",)

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('download_orders/<int:pk>/', self.download_orders),
        ]
        return my_urls + urls

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @staticmethod
    def user_details(obj):
        return mark_safe(
            "{}<br>{} / {}".format(obj.user.user.get_full_name(), obj.user.user.email, obj.user.user.username))

    @staticmethod
    def download_orders(request, pk):

        if not request.user.is_authenticated:
            return redirect('/')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=Cart-{}.csv'.format(now().date())
        writer = csv.writer(response)
        writer.writerow(("Name", "Email", "Phone", "products", "quantity", "created_on", "is_order"))

        queryset = models.Cart.objects.all()

        for obj in queryset:
            is_order = "True" if Orders.objects.filter(user=obj.user, is_success=True) else "False"
            date = obj.created_on.strftime('%Y-%m-%d')
            if int(pk) == 1:
                row_list = [obj.user.user.first_name, obj.user.user.email, obj.user.user.username, obj.product,
                            obj.quantity, date, is_order]
                writer.writerow(row_list)
            else:
                if is_order != "True":
                    row_list = [obj.user.user.first_name, obj.user.user.email, obj.user.user.username, obj.product,
                                obj.quantity, date, is_order, queryset.filter(user=obj.user).count()]

                    writer.writerow(row_list)
        return response
