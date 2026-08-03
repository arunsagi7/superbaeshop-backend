from annoying.functions import get_object_or_None
from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.urls import path

from categories import models
from . import admin_views


class MyAdminSite(admin.AdminSite):
    site_title = "Space And Beauty"
    site_header = "Space And Beauty"
    index_template = "admin_dashboard.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('homebanner/', self.admin_view(admin_views.HomebannerListView.as_view()),
                 name='homebanner_list'),
            path('homebanner/add/', self.admin_view(
                admin_views.HomebannerCreateView.as_view()), name='homebanner_add'),
            path('homebanner/<int:banner_id>/edit/', self.admin_view(
                admin_views.HomebannerEditView.as_view()), name='homebanner_edit'),
            path('homebanner/<int:banner_id>/toggle/', self.admin_view(
                admin_views.HomebannerToggleView.as_view()), name='homebanner_toggle'),
            path('homebanner/<int:banner_id>/delete/', self.admin_view(
                admin_views.HomebannerDeleteView.as_view()), name='homebanner_delete'),
            path('homebanner/product-search/', self.admin_view(
                admin_views.ProductSearchView.as_view()), name='homebanner_product_search'),
        ]
        return custom_urls + urls


my_admin_site = MyAdminSite(name='my_admin')


class SubCategoriesAdminInline(admin.StackedInline):
    model = models.SubCategories
    fields = ("title", "code", "image", "is_active")


class CategoriesImageAdmin(admin.StackedInline):
    model = models.CategoriesImage
    fields = ("image",)


@admin.register(models.Categories, site=my_admin_site)
class CategoriesAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_active")
    inlines = [CategoriesImageAdmin, SubCategoriesAdminInline]
    search_fields = ("title",)

    def has_delete_permission(self, request, obj=None):
        return False


class CategoriesAdminInline(admin.StackedInline):
    model = models.Categories
    fields = ("title", "code", "image", "is_active")


@admin.register(models.SuperCategories, site=my_admin_site)
class SuperCategoriesAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "title", "is_active",)
    list_filter = ("is_active",)

    # inlines = [CategoriesAdminInline]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.ProductTags, site=my_admin_site)
class ProductTagsAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "title", "is_active",)
    list_filter = ("is_active",)

    def has_delete_permission(self, request, obj=None):
        return False


class RateCardForm(forms.ModelForm):

    def clean_from_start(self):
        price_category = get_object_or_None(models.PricingCategories, from_start__lte=self.cleaned_data["from_start"],
                                            to_end__gte=self.cleaned_data["from_start"])
        if self.instance and self.instance == price_category:
            return self.cleaned_data["from_start"]
        if price_category:
            raise ValidationError("{} this Price Range From conflict with another time slot".format(
                self.cleaned_data["from_start"]))

        return self.cleaned_data["from_start"]

    def clean_to_end(self):
        price_category = get_object_or_None(models.PricingCategories, from_start__lte=self.cleaned_data["to_end"],
                                            to_end__gte=self.cleaned_data["to_end"])
        if self.instance and self.instance == price_category:
            return self.cleaned_data["to_end"]

        if price_category:
            if not (self.instance and self.instance != price_category):
                raise ValidationError("{} this Price Range From conflict with another time slot".format(
                    self.cleaned_data["to_end"]))

        return self.cleaned_data["to_end"]


@admin.register(models.PricingCategories, site=my_admin_site)
class CategoriesAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "from_start", "to_end", "code")
    search_fields = ("title",)
    form = RateCardForm

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.PaymentGateWay, site=my_admin_site)
class PaymentGateWayAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Countries, site=my_admin_site)
class CountriesAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "code", "code2", "currency_type",
                    "redeem_point_cash", "shipping_fee", "is_active")
    filter_horizontal = ("available_payment_gateway",)
    search_fields = ("title", "code")
    fieldsets = (
        ("Basic Info", {
            "fields": ("title", ("code", "code2", "dial_code"), ("currency_type", "shipping_fee", "redeem_point_cash"),
                       ("cod_charge", "is_cod_available"), "image", "available_payment_gateway")
        }),
    )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.DesignType, site=my_admin_site)
class DesignTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "slug")

    def has_delete_permission(self, request, obj=None):
        return False


class HomepageSectionProductInline(admin.StackedInline):
    model = models.HomepageSectionProduct
    fields = ("title", "subtitle", "image", "price", "original_price", "link_url",
              "link_text", "rating", "reviews_count", "badge", "ordering", "is_active")
    extra = 1
    verbose_name = "Section Product"
    verbose_name_plural = "Section Products"


@admin.register(models.HomepageSection, site=my_admin_site)
class HomepageSectionAdmin(admin.ModelAdmin):
    list_display = ("section_type", "title", "ordering", "is_active")
    list_editable = ("ordering", "is_active")
    list_filter = ("section_type", "is_active")
    search_fields = ("title",)
    fieldsets = (
        ("Section Info", {
            "fields": ("section_type", "title", "subtitle", "description")
        }),
        ("Media & Style", {
            "fields": ("image", "background_color")
        }),
        ("Link", {
            "fields": ("link_url", "link_text")
        }),
        ("Settings", {
            "fields": ("ordering", "is_active")
        }),
    )
    inlines = [HomepageSectionProductInline]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.ProductDesign, site=my_admin_site)
class DesignTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "code")
    list_display_links = ("id", "title", "code")

    def has_delete_permission(self, request, obj=None):
        return False


class HeroBannerProductInline(admin.StackedInline):
    model = models.HeroBannerProduct
    fields = ("product", "title", "subtitle", "image", "price",
              "original_price", "badge", "ordering", "is_active")
    extra = 1
    verbose_name = "Banner Product"
    verbose_name_plural = "Banner Products"


@admin.register(models.HeroBanner, site=my_admin_site)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ("title", "ordering", "is_active",
                    "section", "video_preview")
    list_editable = ("ordering", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title",)
    fields = ("title", "video", "section", "ordering", "is_active")
    ordering = ("ordering",)
    inlines = [HeroBannerProductInline]

    def video_preview(self, obj):
        if obj.video:
            from django.utils.html import format_html
            return format_html(
                '<video width="120" height="70" controls autoplay loop style="border-radius:6px">'
                '<source src="{}" type="video/mp4">'
                '</video>',
                obj.video.url
            )
        return "No video"
    video_preview.short_description = "Preview"


@admin.register(models.HeroBannerProduct, site=my_admin_site)
class HeroBannerProductAdmin(admin.ModelAdmin):
    list_display = ("title", "banner", "product",
                    "price", "is_active", "ordering")
    list_filter = ("is_active",)
    search_fields = ("title",)
