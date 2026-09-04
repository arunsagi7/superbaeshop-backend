"""
Comprehensive Admin Panel Registration for Space and Beauty
Registers ONLY models that are NOT already registered in their respective app admin.py files.
This file adds missing admin registrations to the custom admin site (my_admin_site).
"""
from django.contrib import admin
from django.utils.safestring import mark_safe

from categories.admin import my_admin_site
from categories.models import CategoriesImage
from product_management.models import ProductImages, ProductVideos, ProductAvailableCountries, ProductContent
from accounts.models import Address, UserPointsHistory
from cart_management.models import GuestCart
from orders_management.models import OrderItems, OrderItemsCancelled, OrderStatus
from offers_management.models import OfferTerms
from affiliate_management.models import AffiliatesReferral
from others.models import ShipmentLogin
from hero.models import HeroVideo, HeroVideoProduct


# ============================================================
# CATEGORIES APP - Additional registrations
# ============================================================

@admin.register(CategoriesImage, site=my_admin_site)
class CategoriesImageAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "image_preview")
    list_select_related = ("category",)
    search_fields = ("category__title",)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="80" height="80" style="object-fit:cover;border-radius:4px" />')
        return "No Image"
    image_preview.short_description = "Preview"


# ============================================================
# PRODUCT MANAGEMENT APP - Additional registrations
# ============================================================

@admin.register(ProductImages, site=my_admin_site)
class ProductImagesAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "title", "image_preview")
    list_select_related = ("product",)
    search_fields = ("title", "product__title")
    list_filter = ("product__category",)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" style="object-fit:cover;border-radius:4px" />')
        return "No Image"
    image_preview.short_description = "Preview"


@admin.register(ProductVideos, site=my_admin_site)
class ProductVideosAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "title", "content_type")
    list_select_related = ("product",)
    search_fields = ("title", "product__title")


@admin.register(ProductAvailableCountries, site=my_admin_site)
class ProductAvailableCountriesAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "country",
                    "original_price", "selling_price")
    list_select_related = ("product", "country")
    search_fields = ("product__title", "country__title")
    list_filter = ("country",)


@admin.register(ProductContent, site=my_admin_site)
class ProductContentAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "heading")
    list_select_related = ("product",)
    search_fields = ("heading", "product__title")


# ============================================================
# CART MANAGEMENT APP - Additional registrations
# ============================================================

@admin.register(GuestCart, site=my_admin_site)
class GuestCartAdmin(admin.ModelAdmin):
    list_display = ("id", "session_id", "product", "quantity", "created_on")
    list_select_related = ("product",)
    search_fields = ("session_id", "product__title")
    list_filter = ("created_on",)


# ============================================================
# ORDERS MANAGEMENT APP - Additional registrations
# ============================================================

@admin.register(OrderItems, site=my_admin_site)
class OrderItemsAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "product_sku",
                    "quantity", "unit_price", "pay_amount")
    list_select_related = ("order", "product", "currency")
    search_fields = (
        "product_sku", "order__tracking_client_id", "product__title")


@admin.register(OrderItemsCancelled, site=my_admin_site)
class OrderItemsCancelledAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product",
                    "product_sku", "quantity", "created_on")
    list_select_related = ("order", "product")
    search_fields = ("product_sku", "order__tracking_client_id")


@admin.register(OrderStatus, site=my_admin_site)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "order_status", "is_active")
    list_select_related = ("order_status",)
    list_filter = ("is_active",)


# ============================================================
# OFFERS MANAGEMENT APP - Additional registrations
# ============================================================

@admin.register(OfferTerms, site=my_admin_site)
class OfferTermsAdmin(admin.ModelAdmin):
    list_display = ("id", "offer", "title")
    list_select_related = ("offer",)


# ============================================================
# AFFILIATE MANAGEMENT APP - Additional registrations
# ============================================================

@admin.register(AffiliatesReferral, site=my_admin_site)
class AffiliatesReferralAdmin(admin.ModelAdmin):
    list_display = ("id", "referred_by", "referral")
    list_select_related = ("referred_by", "referral")


# ============================================================
# OTHERS APP - Additional registrations
# ============================================================
# NOTE: ShipmentLogin (Shiprocket credentials) is registered in
# others/admin.py with token-refresh support.


# ============================================================
# HERO APP - Additional registrations (register to my_admin_site)
# ============================================================

@admin.register(HeroVideo, site=my_admin_site)
class HeroVideoAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "order", "is_active", "video_preview")
    ordering = ("order",)
    list_filter = ("is_active",)

    def video_preview(self, obj):
        if obj.video:
            return mark_safe(
                f'<video width="120" height="70" controls  style="border-radius:6px">'
                f'<source src="{obj.video.url}" type="video/mp4">'
                f'</video>'
            )
        return "No video"
    video_preview.short_description = "Preview"


@admin.register(HeroVideoProduct, site=my_admin_site)
class HeroVideoProductAdmin(admin.ModelAdmin):
    list_display = ("id", "video", "product")
    list_select_related = ("video", "product")


# ============================================================
# ACCOUNTS APP - Additional registrations
# ============================================================

@admin.register(Address, site=my_admin_site)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "door_no", "city",
                    "state", "country", "is_active")
    list_select_related = ("user", "country")
    search_fields = ("city", "state", "door_no", "user__user__username")
    list_filter = ("is_active", "country", "address_type")


@admin.register(UserPointsHistory, site=my_admin_site)
class UserPointsHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "point", "is_credit",
                    "description", "created_on")
    list_select_related = ("user",)
    list_filter = ("is_credit",)
    date_hierarchy = "created_on"
