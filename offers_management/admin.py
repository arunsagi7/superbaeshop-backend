from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin

from categories.admin import my_admin_site
from offers_management import models


@admin.register(models.Coupon, site=my_admin_site)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("offer_code", "title", "payout", "is_active",
                    "created_on", "used_count", "affiliate")

    fieldsets = (
        ('Basic info', {
            'fields': ("offer_code", "title", ("payout", "is_active"))
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return "offer_code",
        return ()

    def used_count(self, offer):
        return offer.user_offer.filter(is_success=True).count()

    @staticmethod
    def affiliate(offer):
        return "{}".format(offer.affiliate_offer)

    def has_delete_permission(self, request, obj=None):
        return False

    used_count.short_description = "Total Used Count"


class OfferTermsAdminInline(admin.StackedInline):
    model = models.OfferTerms
    fields = (("icon", "title"),)
    min_num = 1
    extra = 0


@admin.register(models.Offers, site=my_admin_site)
class OffersAdmin(admin.ModelAdmin):
    list_display = ("type", "title", "short_descriptions",
                    "created_on", "is_active")
    filter_horizontal = ("categories",)
    readonly_fields = ("created_on", "updated_on",)
    search_fields = ("title",)
    date_hierarchy = "created_on"
    inlines = [OfferTermsAdminInline]
    list_filter = ("type", "is_active")

    fieldsets = (
        ('Basic info', {
            'fields': (
                "type", "title", ("min_product", "offer_value",
                                  "max_discount"), "short_descriptions",
                "categories",
                ("is_active", "created_on", "updated_on"),)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False
